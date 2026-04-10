from interfaces.controllers.vocabulary_controller import VocabularyController

def lambda_handler(event, context):
    # look up vocabulary logic here
    ctrl = VocabularyController()
    # return response
    return ctrl.lookup(event)