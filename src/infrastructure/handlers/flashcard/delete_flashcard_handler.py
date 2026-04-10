from interfaces.controllers.flashcard_controller import FlashCardController

def lambda_handler(event, context):
    # celete flashcard logic here
    ctrl = FlashCardController()
    # return response
    return ctrl.delete(event)