import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import threading

class TelegramIO:
    def __init__(self, *args, **kwargs):
        self._output, self._input = None, None

        updater = Updater(kwargs['telegram']['token'])

        updater.dispatcher.add_handler(MessageHandler(Filters.text, self._text_input))

        threading.Thread(target=updater.start_polling, daemon=True).start()
        #updater.idle()


    def input(self, *args, **kwargs):
        while self._input is None:
            time.sleep(0.5)
        text = self._input.strip().lower()
        self._input = None
        assert text is not None
        return text


    def output(self, utterance, *args, **kwargs):
        self._output = utterance


    def _text_input(self, update: Update, context: CallbackContext) -> None:
        self._input = update.message.text
        while self._output is None:
            time.sleep(0.5)
        update.message.reply_text(self._output)
        self._output = None


def main():
    token = load_conf("server.yaml")['telegram']['token']


if __name__ == "__main__":
    main()
