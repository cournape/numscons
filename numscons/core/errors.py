class NumsconsError(Exception):
    pass

class UnknownCompiler(NumsconsError):
    pass

class InternalError(NumsconsError):
    pass
