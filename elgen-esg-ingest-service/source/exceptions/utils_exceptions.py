class UtilsException(Exception):
    """A common error raised by utils"""

    def __init__(self, detail="An exception from utils occurred"):
        self.detail = detail
        super().__init__(self.detail)


class NltkPackageError(UtilsException):
    """An error raised when the punk package is missing"""

    def __init__(self, detail="You need to install NLTK package to chunk your text, for that use the following "
                              "command: nltk.download('punkt')"):
        super().__init__(detail)
