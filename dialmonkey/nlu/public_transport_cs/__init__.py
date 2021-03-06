#!/usr/bin/env python3
# encoding: utf8

import copy
import os
from ast import literal_eval

from ...component import Component
from ...da import DAI, DA
from .database import database
from .preprocessing import CategoryLabelDatabase, Preprocessing
from .string_func import TokenList


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../data/public_transport_cs")


class PublicTransportCSNLU(Component):

    def __init__(self, config):
        super(PublicTransportCSNLU, self).__init__(config)
        if config and 'utt2da' in config:
            self.utt2da = self._load_utt2da(config['utt2da'])
        else:
            self.utt2da = {}
        self.cldb = CategoryLabelDatabase(database)
        self.preprocessing = Preprocessing(self.cldb)

    def _load_utt2da(self, filename):
        """
        Load a dictionary mapping utterances directly to dialogue acts for the utterances
        that are either too complicated or too unique to be parsed by HDC SLU rules.

        :param filename: path to file with a list of utterances transcriptions and corresponding dialogue acts
        :return: a dictionary from utterance to dialogue act
        :rtype: dict
        """
        utt2da = {}
        with open(os.path.join(DATA_DIR, filename), 'r', encoding='UTF-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, val = line.strip().split('\t')
                    utt2da[key.lower()] = DA.parse(val)
        return utt2da

    def abstract_utterance(self, utterance):
        """
        Return a list of possible abstractions of the utterance.

        :param utterance: an Utterance instance
        :return: a list of abstracted utterance, form, value, category label tuples
        """
        abs_utts = copy.deepcopy(utterance)
        category_labels = set()
        abs_utt_lengths = [1] * len(abs_utts)
        start = 0
        while start < len(utterance):
            end = len(utterance)
            while end > start:
                f = tuple(utterance[start:end])

                # found a form
                if f in self.cldb.form2value2cl:
                    # use the 1st matching value (XXX there's no good way of disambiguating)
                    for v in self.cldb.form2value2cl[f]:
                        # get the categories
                        c = self.cldb.form2value2cl[f][v]
                        if not c:  # no categories -- shouldn't happen
                            continue
                        elif len(c) > 1:  # ambiguous categories -- try disambiguating
                            c = self.disambiguate_category(utterance, start, end, c)
                        else:
                            c = c[0]
                        abs_utts = abs_utts.replace(list(f), [c.upper() + '=' + v])
                        abs_utt_lengths[start] = len(f)
                        category_labels.add(c.upper())
                        break
                    # skip all substring for this form
                    start = end
                    break
                end -= 1
            else:
                start += 1
        # normalize abstract utterance lengths
        norm_abs_utt_lengths = []
        i = 0
        while i < len(abs_utt_lengths):
            le = abs_utt_lengths[i]
            norm_abs_utt_lengths.append(le)
            i += le
        return abs_utts, category_labels, norm_abs_utt_lengths

    def disambiguate_category(self, utterance, start, end, categories):
        """Disambiguate categories -- stop/city, stop/train or city/train
        by context, default to 1st one in other cases (which shouldn't happen).
        """
        if sorted(categories) == ['city', 'stop']:
            if utterance[max(0, start - 2):start].any_word_in(
                    ['zast??vka', 'zast??vky', 'zast??vku', 'zast??vce',
                     'zast??vkou', 'stanice', 'stanici', 'stanic??']):
                return 'stop'
            return 'city'
        if 'train_name' in categories and ('city' in categories or 'stop' in categories):
            if utterance[max(0, start - 1):start].any_word_in(
                    ['vlak', 'vlakem', 'vlaku', 'vlaky', 'vlak??', 'vlak??m', 'vlac??ch',
                     'jet', 'jedu', 'jede', 'pojede', 'jezd??', 'jezdit', 'jel', 'ujel',
                     'jela', 'ujela', 'pojedu', 'jelo', 'ujelo']):
                return 'train_name'
            return sorted(categories)[0]
        else:
            return categories[0]

    def parse_stop(self, abutterance, cn):
        """ Detects stops in the input abstract utterance.

        :param abutterance: the input abstract utterance.
        :param cn: The output dialogue act item confusion network.
        """

        # regular parsing
        phr_wp_types = [('from', ['z', 'za', 'ze', 'od', 'za????tek na', 'za????te??n??',
                                  'po????tek na', 'po????te??n?? na', 'v??choz?? na',
                                  'po????te??n??', 'po????tek', 'v??choz??', 'start na', 'stoj??m na',
                                  'jsem na', 'start u', 'stoj??m u', 'jsem u', 'start',
                                  'za????tek u', 'za????tek']),
                        ('to', ['k', 'do', 'konec', 'na', 'kone??n??', 'koncov??',
                                'c??lov??', 'c??l', 'v??stupn??', 'c??l na', 'chci na']),
                        ('via', ['p??es'])]

        self.parse_waypoint(abutterance, cn, 'STOP=', 'stop', phr_wp_types)

    def parse_city(self, abutterance, cn):
        """ Detects stops in the input abstract utterance.

        :param abutterance: the input abstract utterance.
        :param cn: The output dialogue act item confusion network.
        """

        # regular parsing
        phr_wp_types = [('from', ['z', 'ze', 'od', 'za????tek', 'za????te??n??',
                                  'po????te??n??', 'po????tek', 'v??choz??', 'start',
                                  'jsem v', 'stoj??m v', 'za????tek v']),
                        ('to', ['k', 'do', 'konec', 'na', 'kon????m',
                                'c??l', 'vystupuji', 'vystupuju']),
                        ('via', ['p??es', ]),
                        ('in', ['pro', 'po']),
                        ]

        self.parse_waypoint(abutterance, cn, 'CITY=', 'city', phr_wp_types, phr_in=['v', 've'])

    def parse_waypoint(self, abutterance, da, wp_id, wp_slot_suffix, phr_wp_types, phr_in=None):
        """Detects stops or cities in the input abstract utterance
        (called through parse_city or parse_stop).

        :param abutterance: the input abstract utterance.
        :param cn: The output dialogue act item confusion network.
        :param wp_id: waypoint slot category label (e.g. "STOP=", "CITY=")
        :param wp_slot_suffix: waypoint slot suffix (e.g. "stop", "city")
        :param phr_wp_types: set of phrases for each waypoint type
        :param phr_in: phrases for 'in' waypoint type
        """
        u = abutterance
        N = len(u)

        # simple "ne" cannot be included as it collides with negation. "ne [,] chci jet z Motola"
        phr_dai_types = [('confirm', set(['jede to', 'odj????d?? to', 'je v??choz??']), set()),
                         ('deny',
                          # positive matches
                          set(['nechci', 'nejedu', 'ne z', 'ne od', 'ne na', 'ne do', 'n?? do', 'ne k', 'nikoliv', 'nechci na', 'necht??l']),
                          # negative matches
                          set(['nechci ukon??it hovor', 'nechci to tak', 'n?? to nechci', 'ne to nechci', 'nechci n??pov??du',
                               'nechci chci', 'ne to ne', 'ne ne z']))]
        last_wp_pos = 0

        for i, w in enumerate(u):
            if w.startswith(wp_id):
                wp_name = w[len(wp_id):]
                wp_types = set()
                dai_type = 'inform'

                # test short preceding context to find the stop type (from, to, via)
                wp_precontext = {}
                for cur_wp_type, phrases in phr_wp_types:
                    wp_precontext[cur_wp_type] = u[max(last_wp_pos, i - 5): i].first_phrase_span(phrases)
                wp_types |= self._get_closest_wp_type(wp_precontext)
                # test short following context (0 = from, 1 = to, 2 = via)
                if not wp_types:
                    if u[i:i + 3].any_phrase_in(phr_wp_types[0][1] + phr_wp_types[2][1]):
                        wp_types.add('to')
                    elif u[i:i + 3].any_phrase_in(phr_wp_types[1][1]):
                        wp_types.add('from')
                # resolve context according to further preceding/following waypoint name (assuming from-to)
                if not wp_types:
                    if i >= 1 and u[i - 1].startswith(wp_id):
                        wp_types.add('to')
                    elif i <= N - 2 and u[i + 1].startswith(wp_id):
                        wp_types.add('from')
                # using 'in' slot if the previous checks did not work and we have phrases for 'in'
                if not wp_types and phr_in is not None and u[max(last_wp_pos, i - 5): i].any_phrase_in(phr_in):
                    wp_types.add('in')

                # test utterance type
                for cur_dai_type, phrases_pos, phrases_neg in phr_dai_types:
                    if u[last_wp_pos:i].any_phrase_in(phrases_pos) and not u[last_wp_pos:i].any_phrase_in(phrases_neg):
                        dai_type = cur_dai_type
                        break

                # add waypoint to confusion network (standard case: just single type is decided)
                if len(wp_types) == 1:
                    da.append(DAI(dai_type, wp_types.pop() + '_' + wp_slot_suffix, wp_name))
                # backoff 1: add both 'from' and 'to' waypoint slots
                elif 'from' in wp_types and 'to' in wp_types:
                    da.append(DAI(dai_type, 'from_' + wp_slot_suffix, wp_name, 0.501))
                    da.append(DAI(dai_type, 'to_' + wp_slot_suffix, wp_name, 0.499))
                # backoff 2: let the DM decide in context resolution
                else:
                    da.append(DAI(dai_type, wp_slot_suffix, wp_name))

                last_wp_pos = i + 1

    def _get_closest_wp_type(self, wp_precontext):
        """Finds the waypoint type that goes last in the context (if same end points are
        encountered, the type with a longer span wins).

        :param wp_precontext: Dictionary waypoint type -> span (start, end+1) in the preceding \
            context of the waypoint mention
        :returns: one-member set with the best type (if there is one with non-negative position), \
            or empty set on failure
        :rtype: set
        """
        best_type = None
        best_pos = (-2, -1)
        for cur_type, cur_pos in wp_precontext.items():
            if cur_pos[1] > best_pos[1] or cur_pos[1] == best_pos[1] and cur_pos[0] < best_pos[0]:
                best_type = cur_type
                best_pos = cur_pos
        if best_type is not None:
            return set([best_type])
        return set()

    def parse_number(self, abutterance):
        """Detect a number in the input abstract utterance

        Number words that form time expression are collapsed into a single TIME category word.
        Recognized time expressions (where FRAC, HOUR and MIN stands for fraction, hour and minute numbers respectively):
            - FRAC [na] HOUR
            - FRAC hodin*
            - HOUR a FRAC hodin*
            - HOUR hodin* a MIN minut*
            - HOUR hodin* MIN
            - HOUR hodin*
            - HOUR [0]MIN
            - MIN minut*

        Words of NUMBER category are assumed to be in format parsable to int or float

        :param abutterance: the input abstract utterance.
        :type abutterance: Utterance
        """
        def parse_number(word):
            return literal_eval(word[len("NUMBER="):])

        def hour_number(word):
            if not word.startswith("NUMBER="):
                return False
            num = parse_number(word)
            return isinstance(num, int) and 0 <= num < 24

        def minute_number(word):
            if not word.startswith("NUMBER="):
                return False
            num = parse_number(word)
            return isinstance(num, int) and 0 <= num < 60

        def fraction_number(word):
            if not word.startswith("NUMBER="):
                return False
            num = parse_number(word)
            return isinstance(num, float)

        u = abutterance
        i = 0
        while i < len(u):
            if fraction_number(u[i]):
                minute_num = int(parse_number(u[i]) * 60)
                # FRAC na HOUR
                if i < len(u) - 2 and minute_num in [15, 45] and u[i + 1] == 'na' and hour_number(u[i + 2]):
                    u[i:i + 3] = ["TIME_{len}={hour}:{min}".format(len=3, hour=parse_number(u[i + 2]) - 1, min=minute_num)]
                # FRAC HOUR
                if i < len(u) - 1 and minute_num == 30 and hour_number(u[i + 1]):
                    u[i:i + 2] = ["TIME_{len}={hour}:{min}".format(len=2, hour=parse_number(u[i + 1]) - 1, min=minute_num)]
                # FRAC hodin*
                elif i < len(u) - 1 and u[i + 1].startswith('hodin'):
                    u[i:i + 2] = ["TIME_{len}=0:{min}".format(len=2, min=minute_num)]
            elif hour_number(u[i]):
                hour_num = parse_number(u[i])
                # HOUR a FRAC hodin*
                if i < len(u) - 3 and u[i + 1] == 'a' and fraction_number(u[i + 2]) and u[i + 3].startswith('hodin'):
                    u[i:i + 4] = ["TIME_{len}={hour}:{min}".format(len=4, hour=hour_num, min=int(parse_number(u[i + 2]) * 60))]
                if i < len(u) - 1 and u[i + 1].startswith('hodin'):
                    # HOUR hodin* a MIN minut*
                    if i < len(u) - 4 and u[i + 2] == 'a' and minute_number(u[i + 3]) and u[i + 4].startswith('minut'):
                        u[i:i + 5] = ["TIME_{len}={hour}:{min:0>2d}".format(len=5, hour=hour_num, min=parse_number(u[i + 3]))]
                    # HOUR hodin* MIN
                    elif i < len(u) - 3 and minute_number(u[i + 2]):
                        u[i:i + 4] = ["TIME_{len}={hour}:{min:0>2d}".format(len=4, hour=hour_num, min=parse_number(u[i + 2]))]
                    # HOUR hodin*
                    else:
                        u[i:i + 2] = ["TIME_{len}={hour}:00".format(len=2, hour=hour_num)]
                if i < len(u) - 1 and minute_number(u[i + 1]):
                    minute_num = parse_number(u[i + 1])
                    # HOUR MIN
                    if minute_num > 9:
                        u[i:i + 2] = ["TIME_{len}={hour}:{min}".format(len=2, hour=hour_num, min=minute_num)]
                    # HOUR 0 MIN (single digit MIN)
                    elif minute_num == 0 and i < len(u) - 2 and minute_number(u[i + 2]) and parse_number(u[i + 2]) <= 9:
                        u[i:i + 3] = ["TIME_{len}={hour}:{min:0>2d}".format(len=3, hour=hour_num, min=parse_number(u[i + 2]))]
            if minute_number(u[i]):
                # MIN minut*
                if i < len(u) - 1 and u[i + 1].startswith("minut"):
                    u[i:i + 2] = ["TIME_{len}=0:{min:0>2d}".format(len=2, min=parse_number(u[i]))]

            if i > 0:
                # v HOUR
                if u[i - 1] == 'v' and hour_number(u[i]):
                    u[i] = "TIME_{len}={hour}:00".format(len=1, hour=parse_number(u[i]))
                # za hodinu/minutu
                elif u[i - 1] == 'za':
                    if u[i] == 'hodinu':
                        u[i] = "TIME_1=1:00"
                    elif u[i] == 'minutu':
                        u[i] = "TIME_1=0:01"
            i += 1

    def parse_time(self, abutterance, da):
        """Detects the time in the input abstract utterance.

        :param abutterance: the input abstract utterance.
        :param da: The output dialogue act item confusion network.
        """

        u = abutterance

        # preps_abs = set(["v", "ve", "??as", "o", "po", "p??ed", "kolem"])
        preps_rel = set(["za", ])

        test_context = [('confirm', 'departure',
                         ['jede to', 'odj????d?? to', 'je v??choz??', 'm?? to odjezd', 'je odjezd', 'pojede to'],
                         []),
                        ('confirm', 'arrival',
                         ['p??ijede to', 'p??ij????d?? to', 'm?? to p????jezd', 'je p????jezd'],
                         []),
                        ('confirm', '',
                         ['je to', 'mysl??te', 'mysl????'],
                         []),
                        ('deny', 'departure',
                         ['nechci jet', 'nejedu', 'nechci odj????d??t', 'nechci odjezd', 'nechci vyjet', 'nechci vyj????d??t',
                          'nechci vyr????et', 'nechci vyrazit'],
                         []),
                        ('deny', 'arrival',
                         ['nechci p??ijet', 'nechci p??ij????d??t', 'nechci p????jezd', 'nechci dorazit'],
                         []),
                        ('deny', '',
                         ['ne', 'nechci'],
                         []),
                        ('inform', 'departure',
                         ['TASK=find_connection', 'odjezd', 'odj????det', 'odj????d??t', 'odj????d??t v', 'odj????d??', 'odjet',
                          'jedu', 'jede', 'vyr??????m', 'vyr????et', 'vyrazit', 'bych jel', 'bych jela', 'bych jet',
                          'bych tam jel', 'bych tam jela', 'bych tam jet',
                          'abych jel', 'abych jela', 'jak se dostanu', 'kdy jede', 'jede n??jak??',
                          'jede n??jak??', 'VEHICLE=tram', 'chci jet', 'cht??l jet', 'cht??la jet'],
                         ['p????jezd', 'p??ijet', 'dorazit', 'abych p??ijel', 'abych p??ijela', 'chci b??t', 'cht??l bych b??t']),
                        ('inform', 'arrival',
                         ['p????jezd', 'p??ijet', 'dorazit', 'abych p??ijel', 'abych p??ijela', 'chci b??t', 'cht??l bych b??t'],
                         []),
                        ('inform', '',
                         [],
                         []),
                        ]

        count_times = 0
        for i, w in enumerate(u):
            if w.startswith("TIME_") or w.startswith("TIME="):
                count_times += 1

        last_time_type = ''
        last_time = 0

        for i, w in enumerate(u):
            if w.startswith("TIME_") or w.startswith("TIME="):
                if w.startswith("TIME_"):
                    value = w[7:]
                else:
                    value = w[5:]
                time_rel = False

                if i >= 1:
                    if u[i - 1] in preps_rel:
                        time_rel = True

                if count_times > 1:
                    j, k = last_time, i
                else:
                    j, k = 0, len(u)

                if value == "now":
                    if u[j:k].any_phrase_in(['no a', 'kolik je', 'nesly????m', 'u?? mi ne????k??']):
                        continue
                    else:
                        time_rel = True

                for act_type, time_type, phrases_pos, phrases_neg in test_context:
                    if u[j:k].any_phrase_in(phrases_pos) and not u.any_phrase_in(phrases_neg):
                        break

                if count_times > 1 and not time_type:
                    # use the previous type if there was time before this one
                    time_type = last_time_type
                last_time_type = time_type

                slot = (time_type + ('_time_rel' if time_rel else '_time')).lstrip('_')
                da.append(DAI(act_type, slot, value))
                last_time = i + 1

    def parse_date_rel(self, abutterance, da):
        """Detects the relative date in the input abstract utterance.

        :param abutterance: the input abstract utterance.
        :param da: The output dialogue act item confusion network.
        """
        u = abutterance

        for i, w in enumerate(u):
            if w.startswith("DATE_REL="):
                value = w[9:]

                confirm = u[max(i - 5, 0):i].any_phrase_in(['jede to', 'odj????d?? to', 'pojede to', 'm?? to odjezd', 'je odjezd'])
                deny = u[max(i - 5, 0):i].any_word_in(['nechci', 'ale ne'])

                if confirm:
                    dai = DAI("confirm", 'date_rel', value)
                elif deny:
                    dai = DAI("deny", 'date_rel', value)
                else:
                    dai = DAI("inform", 'date_rel', value)

                if dai not in da:
                    da.append(dai)

    def parse_ampm(self, abutterance, da):
        """Detects the ampm in the input abstract utterance.

        :param abutterance: the input abstract utterance.
        :param da: The output dialogue act item confusion network.
        """
        u = abutterance

        for i, w in enumerate(u):
            if w.startswith("AMPM="):
                value = w[5:]
                confirm = u[max(i - 5, 0):i].any_phrase_in(['jede to', 'odj????d?? to', 'pojede to', 'm?? to odjezd', 'je odjezd'])
                deny = u[max(i - 5, 0):i].any_word_in(['nechci', 'ale ne'])

                if not (u.phrase_in('dobrou')):
                    if confirm:
                        da.append(DAI("confirm", 'ampm', value))
                    elif deny:
                        da.append(DAI("deny", 'ampm', value))
                    else:
                        da.append(DAI("inform", 'ampm', value))

    def parse_vehicle(self, abutterance, da):
        """Detects the vehicle (transport type) in the input abstract utterance.

        :param abutterance: the input abstract utterance.
        :param da: The output dialogue act item confusion network.
        """

        u = abutterance

        confirm = u.phrase_in('jede to')
        deny = u.any_phrase_in(['nechci jet', 'bez pou??it??'])

        for i, w in enumerate(u):
            if w.startswith("VEHICLE="):
                value = w[8:]

                if confirm:
                    da.append(DAI("confirm", 'vehicle', value))
                elif deny:
                    da.append(DAI("deny", 'vehicle', value))
                else:
                    da.append(DAI("inform", 'vehicle', value))

    def parse_task(self, abutterance, da):
        """Detects the task in the input abstract utterance.

        :param abutterance: the input abstract utterance.
        :param da: The output dialogue act item confusion network.
        """

        u = abutterance
        deny = u.phrase_in(['nechci', 'nehled??m'])
        for i, w in enumerate(u):
            if w.startswith("TASK="):
                value = w[5:]
                if deny:
                    da.append(DAI("deny", 'task', value))
                else:
                    da.append(DAI("inform", 'task', value))

    def parse_train_name(self, abutterance, da):
        """Detects the train name in the input abstract utterance.

        :param abutterance:
        :param da:
        """
        category_label = "TRAIN_NAME="

        u = abutterance

        for i, w in enumerate(u):
            if w.startswith(category_label):
                value = w[len(category_label):]

                da.append(DAI("inform", 'train_name', value))

    def parse_non_speech_events(self, utt, da):
        """
        Processes non-speech events in the input utterance.

        :param utt: the input utterance
        :param da: The output dialogue act item confusion network.
        :return: None
        """
        if len(utt) == 0 or utt == "_silence_" or utt == "__silence__" or utt == "_sil_":
            da.append(DAI("silence"))

        if utt == "_noise_" or utt == "_laugh_" or utt == "_ehm_hmm_" or utt == "_inhale_":
            da.append(DAI("null"))

        if utt == "_other_" or utt == "__other__":
            da.append(DAI("other"))

    def parse_meta(self, utt, abutt_lenghts, da):
        """
        Detects all dialogue acts which do not generalise its slot values using CLDB.

        :param utterance: the input utterance
        :param da: The output dialogue act item confusion network.
        :return: None
        """
        if (utt.any_word_in('ahoj ??hoj nazdar zdar') or utt.all_words_in('dobr?? den')):
            da.append(DAI("hello"))

        if (utt.any_word_in("nashledanou shledanou schledanou shle nashle sbohem bohem zbohem zbohem konec hledanou "
                            "naschledanou shledan??") or utt.phrase_in("dobrou noc")
                or (not utt.any_word_in("nechci") and utt.phrase_in("ukon??it hovor"))):
            da.append(DAI("bye"))

        if len(utt) == 1 and utt.any_word_in("??au ??auky ??aues"):
            da.append(DAI("bye"))

        if not utt.any_word_in('spojen?? zast??vka stanice mo??nost varianta'):
            if utt.any_word_in('jin?? jin?? jin?? jin??ho'):
                da.append(DAI("reqalts"))

        if (utt.any_word_in("od za????t za??neme za??n??me za??ni za??n??te") and utt.any_word_in("za????tku znova znovu")
                or utt.any_word_in("reset resetuj restart restartuj zru??it")
                or not utt.any_word_in("ze") and utt.any_phrase_in(['nov?? spojen??', 'nov?? spojen??', 'nov?? zad??n??', 'nov?? zad??n??', 'nov?? spoj'])
                or utt.all_words_in("tak jinak") or utt.any_phrase_in(["tak znova", 'zkus??me to je??t?? jednou'])):
            da.append(DAI("restart"))
        else:
            if not utt.any_word_in('spojen?? zast??vka stanice mo??nost spoj nab??dnut?? posledn?? nalezen?? opakuji'):
                if (utt.any_word_in('zopakovat opakovat znova znovu opakuj zopakuj zopakujte zvopakovat')
                        or utt.phrase_in("je??t?? jednou")):
                    da.append(DAI("repeat"))
            elif utt.any_word_in("zopakuj zopakujte zopakovat opakovat") and utt.phrase_in("posledn?? v??tu"):
                da.append(DAI("repeat"))

        if ((len(utt) == 1 and utt.any_word_in("pardon pard??n promi??te promi?? sorry"))
                or utt.any_phrase_in(['omlouv??m se', 'je mi l??to'])):
            da.append(DAI("apology"))

        if not utt.any_word_in("nechci d??kuji"):
            if (utt.any_word_in("n??pov??da n??pov??du pomoc pomoct pomoci pomo?? pomohla pomohl pom????ete help nev??m nevim nech??pu")
                    or utt.any_word_in('co') and utt.any_word_in("zeptat ????ct d??lat")):
                da.append(DAI("help"))

        if (utt.any_word_in("nesly????me nesly????m halo hal?? nefunguje co??e")
                or not utt.phrase_in("ano sly????me se") and utt.phrase_in("sly????me se")):
            da.append(DAI('canthearyou'))

        if (utt.all_words_in("nerozum??l jsem")
                or utt.all_words_in("nerozum??la jsem")
                or utt.all_words_in("taky nerozum??m")
                or utt.all_words_in("nerozum??m v??m")
                or (len(utt) == 1 and utt.any_word_in("nerozum??m"))):
            da.append(DAI('notunderstood'))

        if not utt.any_word_in("nerozum??j nechci vzd??v??m ??au mo??nost konec") and utt.any_word_in("ano jo jasn?? jojo"):
            da.append(DAI("affirm"))

        if not utt.any_phrase_in(['ne z', 'n?? do']):
            if (utt.any_word_in("ne n?? nene nen?? n????")
                    or utt.any_phrase_in(['nechci to tak', 'to nechci', 'to nehledej', 'no nebyli'])
                    or len(utt) == 1 and utt.any_word_in("nejedu nechci")
                    or len(utt) == 2 and utt.all_words_in("ano nechci")
                    or utt.all_words_in("to je ??patn??")):
                da.append(DAI("negate"))

        if utt.any_word_in('d??ky dikec d??kuji dekuji d??kuju d??kuj??'):
            da.append(DAI("thankyou"))

        if (not utt.any_word_in("ano")
            and (utt.any_word_in('ok po????dku dob??e spr??vn?? sta???? super fajn rozum??l rozum??la sly????m')
                 or utt.any_phrase_in(['to je v??e', 'je to v??e', 'je to v??echno', 'to bylo v??echno', 'to bude v??echno',
                                       'u?? s ni????m', 'u?? s ni??im', 'to jsem cht??l sly??et'])
                 or (not utt.any_phrase_in(['dobr?? den', 'dobr?? d??n', 'dobr?? ve??er']) and utt.any_word_in("dobr??")))):
            da.append(DAI("ack"))

        if utt.any_phrase_in(['chci jet', 'cht??la jet', 'bych jet', 'bych jel', 'bychom jet',
                              'bych tam jet', 'jak se dostanu', 'se dostat']) \
                or utt.any_word_in("trasa, trasou, trasy, trasu, trase"):
            da.append(DAI('inform', 'task', 'find_connection'))

        if utt.any_phrase_in(['jak bude', 'jak dnes bude', 'jak je', 'jak tam bude']):
            da.append(DAI('inform', 'task', 'weather'))

        if utt.any_word_in('n??stupi??t?? kolej koleje'):
            da.append(DAI("inform", "task", "find_platform"))

        if (utt.all_words_in('od to jede')
                or utt.all_words_in('z jake jede')
                or utt.all_words_in('z jak?? jede')
                or utt.all_words_in('z jak?? zast??vky')
                or utt.all_words_in('jak?? v??choz??')
                or utt.all_words_in('kde za????tek')
                or utt.all_words_in('odkud to jede')
                or utt.all_words_in('odkud jede')
                or utt.all_words_in('odkud pojede')
                or utt.all_words_in('od kud pojede')):
            da.append(DAI('request', 'from_stop'))

        if (utt.all_words_in('kam to jede')
                or utt.all_words_in('na jakou jede')
                or utt.all_words_in('do jake jede')
                or utt.all_words_in('do jak?? jede')
                or utt.all_words_in('do jak?? zast??vky')
                or utt.all_words_in('co c??l')
                or utt.all_words_in('jak?? c??lov??')
                or utt.all_words_in('kde kone??n??')
                or utt.all_words_in('kde kone??n??')
                or utt.all_words_in("kam jede")
                or utt.all_words_in("kam pojede")):
            da.append(DAI('request', 'to_stop'))

        if not utt.any_word_in('za budu bude budem p??ijede p??ijedete p??ijedu dojedu dojede doraz?? doraz??m doraz??te'):
            if (utt.all_words_in("kdy jede")
                    or utt.all_words_in("v kolik jede")
                    or utt.all_words_in("v kolik hodin")
                    or utt.all_words_in("kdy to pojede")
                    or (utt.any_word_in('kdy kolik') and utt.any_word_in('jede odj????d?? odjede odj????d???? odj????d??te'))
                    or utt.phrase_in('??asov?? ??daj')):
                da.append(DAI('request', 'departure_time'))

        if not utt.any_word_in('budu bude budem p??ijede p??ijedete p??ijedu dojedu doraz?? doraz??m doraz??te'):
            if (utt.all_words_in("za jak") and utt.any_word_in('dlouho dl??ho')
                    or utt.all_words_in("za kolik minut jede")
                    or utt.all_words_in("za kolik minut pojede")
                    or utt.all_words_in("za jak pojede") and utt.any_word_in('dlouho dl??ho')):
                da.append(DAI('request', 'departure_time_rel'))

        if ((utt.all_words_in('kdy tam') and utt.any_word_in('budu bude budem'))
                or (utt.all_words_in('v kolik') and utt.any_word_in('budu bude budem'))
                or utt.all_words_in('??as p????jezdu')
                or (utt.any_word_in('kdy kolik') and utt.any_word_in('p????jezd p??ijede p??ijedete p??ijedu p??ijedem '
                                                                     'or dojedu doraz?? dojede doraz??m doraz??te'))):
            da.append(DAI('request', 'arrival_time'))

        if (utt.all_words_in('za jak') and utt.any_word_in('dlouho dl??ho')
                and utt.any_word_in('budu bude budem p??ijedu p??ijede p??ijedem p??ijedete dojedu doraz?? doraz??m doraz??te')
                and utt.any_phrase_in(['tam', 'v c??li', 'do c??le', 'k c??li', 'c??lov?? zast??vce', 'c??lov?? stanici'])):
            da.append(DAI('request', 'arrival_time_rel'))

        if not utt.any_word_in('za v p??estup p??estupy'):
            if (utt.all_words_in('jak') and utt.any_word_in('dlouho dl??ho') and utt.any_word_in("jede pojede trv?? trvat")
                    or utt.all_words_in("kolik minut") and utt.any_word_in("jede pojede trv?? trvat")):
                da.append(DAI('request', 'duration'))

        if (utt.all_words_in('kolik je hodin')
                or utt.all_words_in('kolik m??me hodin')
                or utt.all_words_in('kolik je te??')
                or utt.all_words_in('kolik je te??ka')):
            da.append(DAI('request', 'current_time'))

        if utt.any_word_in('p??estup?? p??estupu p??estupy stup???? p??estup p??estupku p??estupky p??estupk?? '
                           'p??estupovat p??estupuju p??estupuji p??estupov??n?? p??estupama p??estupem'):
            if utt.any_word_in('??as ??asu dlouho trv?? trvaj?? trvat'):
                da.append(DAI('request', 'time_transfers'))
            elif utt.any_word_in('kolik po??et kolikr??t jsou je'):
                da.append(DAI('request', 'num_transfers'))
            elif utt.any_word_in('nechci bez ????dn?? ????dn?? ????den'):
                da.append(DAI('inform', 'num_transfers', '0'))
            elif utt.any_word_in('jeden jedn??m jednou'):
                da.append(DAI('inform', 'num_transfers', '1'))
            elif utt.any_word_in('dva dv??ma dv??mi dvakr??t'):
                da.append(DAI('inform', 'num_transfers', '2'))
            elif utt.any_word_in('t??i t??ema t??emi t??ikr??t'):
                da.append(DAI('inform', 'num_transfers', '3'))
            elif utt.any_word_in('??ty??i ??ty??ma ??ty??mi ??ty??ikr??t'):
                da.append(DAI('inform', 'num_transfers', '4'))
            elif (utt.any_word_in('libovoln?? libovoln?? libovoln??')
                  or utt.all_words_in('bez ohledu')  # TODO: This cannot ever get triggered.
                  or utt.any_phrase_in(['s p??estupem', 's p??estupy', 's p??estupama'])):
                da.append(DAI('inform', 'num_transfers', 'dontcare'))

        if utt.any_phrase_in(['p????m?? spoj', 'p????m?? spojen??', 'p????m?? spoje', 'p????m?? spoje', 'p????mej spoj',
                              'p????m?? spojen??', 'jet p????mo', 'pojedu p????mo', 'dostanu p????mo', 'dojedu p????mo',
                              'dostat p????mo']):
            da.append(DAI('inform', 'num_transfers', '0'))

        if utt.any_word_in('spoj spojen?? spoje mo??nost mo??nosti varianta alternativa cesta cestu cesty '
                           'zpo??d??n?? sta??en?? nalezen?? nab??dnut??'):
            if not utt.any_word_in('prvn?? jedna druh?? druh?? t??et?? ??tvrt?? ??tvrt??') and utt.any_word_in('libovoln??'):
                da.append(DAI("inform", "alternative", "dontcare"))

            if (not utt.any_word_in('druh?? druh?? t??et?? ??tvrt?? ??tvrt??') and not utt.all_words_in('je??t?? jedna')
                    and utt.any_word_in('prvn?? jedna')):
                da.append(DAI("inform", "alternative", "1"))

            if not utt.any_word_in('t??et?? ??tvrt?? ??tvrt?? dal????') and utt.any_word_in('druh?? druh?? druh?? druhou dva'):
                da.append(DAI("inform", "alternative", "2"))

            if utt.any_word_in('t??et?? t??i'):
                da.append(DAI("inform", "alternative", "3"))

            if utt.any_word_in('??tvrt?? ??tvrt?? ??tvrt?? ??tvrtou ??ty??i'):
                da.append(DAI("inform", "alternative", "4"))

            if utt.any_word_in('p??t?? p??tou'):
                da.append(DAI("inform", "alternative", "5"))

            if utt.any_word_in("p??edchoz?? p??ed"):
                if utt.any_phrase_in(["nechci v??d??t p??edchoz??", "nechci p??edchoz??"]):
                    da.append(DAI("deny", "alternative", "prev"))
                else:
                    da.append(DAI("inform", "alternative", "prev"))

            elif utt.any_word_in("posledn?? znovu znova opakovat zopakovat zopakujte zopakov??n??"):
                if utt.any_phrase_in(["nechci posledn??"]):
                    da.append(DAI("deny", "alternative", "last"))
                else:
                    da.append(DAI("inform", "alternative", "last"))

            elif (utt.any_word_in("dal???? jin?? jin?? n??sleduj??c?? pozd??j????")
                    or utt.any_phrase_in(['je??t?? jedno', 'je??t?? jednu', 'je??t?? jedna', 'je??t?? jednou', 'je??t?? zeptat na jedno'])):
                da.append(DAI("inform", "alternative", "next"))

        if ((len(utt) == 1 and utt.any_word_in('dal???? n??sleduj??c?? n??sleduj?? pozd??ji'))
                or utt.ending_phrases_in(['dal????', 'co d??l'])):
            da.append(DAI("inform", "alternative", "next"))

        if len(utt) == 2 and (utt.all_words_in("a dal????") or utt.all_words_in("a pozd??ji")):
            da.append(DAI("inform", "alternative", "next"))

        if len(utt) == 1 and utt.any_word_in("p??edchoz?? p??ed"):
            da.append(DAI("inform", "alternative", "prev"))

        if utt.any_phrase_in(["jako v dne", "jako ve dne"]):
            da.append(DAI('inform', 'ampm', 'pm'))

        if utt.ending_phrases_in(["od", "z", "z n??dra????"]):
            da.append(DAI('inform', 'from', '*'))
        elif utt.ending_phrases_in(["na", "do", "d??"]):
            da.append(DAI('inform', 'to', '*'))
        elif utt.ending_phrases_in(["z zast??vky", "z stanice", "v??choz?? stanice je", "v??choz?? zast??vku"]):
            da.append(DAI('inform', 'from_stop', '*'))
        elif utt.ending_phrases_in(["na zast??vku", "n?? zast??vk??", "do zast??vky", "do z??stavky", "do zastavky"]):
            da.append(DAI('inform', 'to_stop', '*'))
        elif utt.ending_phrases_in(["p??es"]):
            da.append(DAI('inform', 'via', '*'))

    def handle_false_abstractions(self, abutterance):
        """
        Revert false positive alarms of abstraction

        :param abutterance: the abstracted utterance
        :return: the abstracted utterance without false positive abstractions
        """
        abutterance = abutterance.replace(['STOP=Metra'], ['metra'])
        abutterance = abutterance.replace(['STOP=N??dra????'], ['n??dra????'])
        abutterance = abutterance.replace(['STOP=SME'], ['sme'])
        abutterance = abutterance.replace(['STOP=B??l?? Hora', 'STOP=??elezni??n?? stanice'],
                                          ['STOP=B??l?? Hora', '??elezni??n?? stanice'])
        abutterance = abutterance.replace(['TIME=now', 'bych', 'cht??l'], ['te??', 'bych', 'cht??l'])
        abutterance = abutterance.replace(['STOP=????m', 'se'], ['????m', 'se'])
        abutterance = abutterance.replace(['STOP=Lu??in', 'STOP=Na Chmelnici'], ['STOP=Lu??in', 'na', 'STOP=Chmelnici'])
        abutterance = abutterance.replace(['STOP=Kone??n??', 'zast??vka'], ['kone??n??', 'zast??vka'])
        abutterance = abutterance.replace(['STOP=Kone??n??', 'STOP=And??l'], ['kone??n??', 'STOP=And??l'])
        abutterance = abutterance.replace(['STOP=Kone??n?? stanice', 'STOP=L??dv??'], ['kone??n??', 'stanice', 'STOP=L??dv??'])
        abutterance = abutterance.replace(['STOP=V??stupn??', 'stanice', 'je'], ['v??stupn??', 'stanice', 'je'])
        abutterance = abutterance.replace(['STOP=Nov??', 'jin??'], ['nov??', 'jin??'])
        abutterance = abutterance.replace(['STOP=Nov??', 'spojen??'], ['nov??', 'spojen??'])
        abutterance = abutterance.replace(['STOP=Nov??', 'zad??n??'], ['nov??', 'zad??n??'])
        abutterance = abutterance.replace(['STOP=Nov??', 'TASK=find_connection'], ['nov??', 'TASK=find_connection'])
        abutterance = abutterance.replace(['z', 'CITY=Liberk'], ['z', 'CITY=Liberec'])
        abutterance = abutterance.replace(['do', 'CITY=Liberk'], ['do', 'CITY=Liberec'])
        abutterance = abutterance.replace(['pauza', 'hrozn??', 'STOP=Dlouh??'], ['pauza', 'hrozn??', 'dlouh??'])
        abutterance = abutterance.replace(['v', 'STOP=Praga'], ['v', 'CITY=Praha'])
        abutterance = abutterance.replace(['na', 'STOP=Praga'], ['na', 'CITY=Praha'])
        abutterance = abutterance.replace(['po', 'STOP=Praga', 'ale'], ['po', 'CITY=Praha'])
        abutterance = abutterance.replace(['jsem', 'v', 'STOP=Metra'], ['jsem', 'v', 'VEHICLE=metro'])
        return abutterance

    def __call__(self, dial, logger):
        """Parse an utterance into a dialogue act.

        :rtype DialogueActConfusionNetwork
        """
        utterance = dial['user']

        logger.debug(f'Parsing utterance "{utterance}"')

        res_da = DA()

        dict_da = self.utt2da.get(str(utterance).lower(), None)
        if dict_da:
            dial['nlu'] = dict_da
            return dial

        utterance = self.preprocessing.normalize(TokenList(utterance.lower()))
        abutterance, category_labels, abutterance_lenghts = self.abstract_utterance(utterance)

        logger.debug(f'After preprocessing: "{abutterance}"')
        logger.debug(category_labels)

        self.parse_non_speech_events(utterance, res_da)

        abutterance = self.handle_false_abstractions(abutterance)
        category_labels.add('CITY')
        category_labels.add('VEHICLE')
        category_labels.add('NUMBER')

        if len(res_da) == 0:
            if 'STOP' in category_labels:
                self.parse_stop(abutterance, res_da)
            if 'CITY' in category_labels:
                self.parse_city(abutterance, res_da)
            if 'NUMBER' in category_labels:
                self.parse_number(abutterance)
                if any([word.startswith("TIME") for word in abutterance]):
                    category_labels.add('TIME')
            if 'TIME' in category_labels:
                self.parse_time(abutterance, res_da)
            if 'DATE_REL' in category_labels:
                self.parse_date_rel(abutterance, res_da)
            if 'AMPM' in category_labels:
                self.parse_ampm(abutterance, res_da)
            if 'VEHICLE' in category_labels:
                self.parse_vehicle(abutterance, res_da)
            if 'TASK' in category_labels:
                self.parse_task(abutterance, res_da)
            if 'TRAIN_NAME' in category_labels:
                self.parse_train_name(abutterance, res_da)

            self.parse_meta(utterance, abutterance_lenghts, res_da)

        res_da.merge_duplicate_dais()
        dial['nlu'] = res_da
        return dial
