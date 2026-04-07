from application.exceptions.application_errors import ApplicationError


class FlashCardError(ApplicationError):
    pass

class InvalidUserId(FlashCardError):
    pass