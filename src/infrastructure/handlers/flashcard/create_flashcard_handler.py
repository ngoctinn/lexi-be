from interfaces.controllers.flashcard_controller import FlashCardController

def handler(event, context):
    # create flashcard logic here
    ctrl = FlashCardController()
    # return response
    return ctrl.create(event)