import yaml
import random
from dialmonkey.component import Component
from dialmonkey.dialogue import Dialogue
from itertools import groupby


def parse_pattern(pattern):
    #TODO check validity

    intent, slot, value = None, None, None

    pattern = pattern[:-1]
    intent, rest = pattern.split('(', maxsplit=1)
    if len(rest) > 0:
        split = rest.split('=')
        if len(split) == 1:
            slot = split[0]
        else:
            slot, value = split

    return intent, slot, value


def match(intent, slot, values, p_intent, p_slot, p_value):
    if intent != p_intent:
        return False
    if p_slot is None and slot is not None:
        return False
    if p_value is None and values is not None and values != [None]:
        return False
    if slot != p_slot:
        if slot is None or p_slot is None:
            return False
        if p_slot[0] == '{':
            if slot not in p_slot[1:-1].split('|'):
                return False
        elif p_slot[0] == '(':
            pass
        else:
            return False
    if p_value is None:
        return True
    if len(values) == 1 and p_value[0] == '{':
        if values[0] not in p_slot[1:-1].split('|'):
            return False
    if p_value[0] != '(' and p_value[0] != '[' and len(values) == 1:
        return p_value == values[0]
    return True


def translate(template, intent, slot, values, p_intent, p_slot, p_value):
    # dont look at this
    if p_slot is not None and p_slot[0] == '{':
        index = p_slot[1:-1].split('|').index(slot)
        template_before, rest = template.split('{', maxsplit=1)
        meat, template_after = rest.split('}', maxsplit=1)
        keyword = meat.split('|')[index]
        pattern = '{' + meat + '}'
        result = template.replace(pattern, keyword)
    else:
        try:
            result = template.replace(p_slot, slot)
        except:
            result = template
    try:
        result = result.replace(p_value, ', '.join(values))
    except:
        pass
    return result


class TemplateNLG(Component):
    def __init__(self, *args, **kwargs):
        with open("dialmonkey/nlg/twitter.yaml", "r") as f:
            self._nlg = yaml.safe_load(f)
        self._nlg = {parse_pattern(k): v for k, v in self._nlg.items()}

        super().__init__(*args, **kwargs)


    def __call__(self, dial: Dialogue, logger):
        assert dial.action is not None
        if len(dial.action) == 0:
            dial.set_system_response("<EMPTY>")
            return dial

        response = ""

        dais = dial.action.dais[:]
        dais.sort(key=lambda x: (str(x.intent), str(x.slot), str(x.value)))
        grouped = groupby(dais, key=lambda x:(str(x.intent), str(x.slot)))

        for (intent, slot), group in grouped:
            group = list(group)
            intent, slot, values = group[0].intent, group[0].slot, list(map(lambda x: x.value, group))
            for pattern, templates in self._nlg.items():
                if match(intent, slot, values, *pattern):
                    template = random.choice(templates)
                    response += translate(template, intent, slot, values, *pattern) + " "
                    break

        dial.set_system_response(response)
        return dial
