class OopsNoDBError(Exception):
    """Raised when DB is not running"""

    def __init__(self, message="No DB is found"):
        self.message = message
        super().__init__(self.message)


class ModelServiceConnectionError(Exception):
    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)


class ModelServiceParsingError(Exception):
    """
    Raise when there is an error parsing a response from a model service
    """

    def __init__(self, message="Unable to get the generated answer!"):
        self.message = message
        super().__init__(self.message)


class DataLayerError(Exception):
    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)


class ChatServiceError(Exception):
    def __init__(self, message="Internal Error!"):
        self.message = message
        super().__init__(self.message)


class DatabaseConnectionError(Exception):
    def __init__(self, message: str = "Database connection error"):
        self.message = message
        super().__init__(self.message)


class DatabaseIntegrityError(Exception):
    def __init__(self, message: str = "Database integrity error"):
        self.message = message
        super().__init__(self.message)


class ConversationFetchDataError(Exception):
    def __init__(self, message: str = "Unable to get conversation"):
        self.message = message
        super().__init__(self.message)


class ConversationValidationError(Exception):
    def __init__(self, message: str = "Conversation schema validation error"):
        self.message = message
        super().__init__(self.message)


class ConversationNotFoundError(Exception):
    def __init__(self, message: str = "Conversation not found"):
        self.message = message
        super().__init__(self.message)


class SourceDocumentsFetchDataError(Exception):
    def __init__(self, message: str = "Unable to get source doc"):
        self.message = message
        super().__init__(self.message)


class SourceDocumentsValidationError(Exception):

    def __init__(self, message: str = "Source document schema validation error"):
        self.message = message
        super().__init__(self.message)


class SourceDocumentsNotFoundError(Exception):
    def __init__(self, message: str = "Source doc not found"):
        self.message = message
        super().__init__(self.message)


class ChatIncompleteDataError(Exception):
    def __init__(self, message: str = "Chat data is incomplete"):
        self.message = message
        super().__init__(self.message)


class ChatAnswerCreationError(Exception):
    def __init__(self, message: str = "Failed to create answer"):
        self.message = message
        super().__init__(self.message)


class AnswerNotFoundException(Exception):
    def __init__(self, message: str = "Answer not found!"):
        """
        raise when db fails to find an answer object but not necessarily want to raise an error
        """
        self.message = message
        super().__init__(self.message)


class AnswerNotFoundError(Exception):
    def __init__(self, message: str = "Answer not found!"):
        """
        raise when db fails to find an answer object
        """
        self.message = message
        super().__init__(self.message)


class VersionedAnswerNotFoundException(Exception):
    def __init__(self, message: str = "Versioned Answer not found!"):
        """
        raise when db fails to find an older version of a given answer
        """
        self.message = message
        super().__init__(self.message)


class PactVerificationError(Exception):
    def __init__(self, message="error in pact verifier"):
        self.message = message
        super().__init__(self.message)


class PactVerifierNotFoundError(Exception):
    def __init__(self, message="pact verifier is not found"):
        self.message = message
        super().__init__(self.message)


class InteractionNotFoundError(Exception):
    def __init__(self, message="pact interaction is not found"):
        self.message = message


class ChatModelDiscoveryError(Exception):
    def __init__(self, model_code: str):
        """
        raised a model code does not correspond to a chat model
        """
        self.message = f"No model route was found for the following model code {model_code}"
        super().__init__(self.message)


class ClassificationModelRetrievalError(Exception):
    def __init__(self, message: str = "Could not get classification model"):
        """
        raised when a getting a Model fails
        """
        self.message = message
        super().__init__(self.message)


class ModelRetrievalError(Exception):
    def __init__(self, message: str = "Could not get model"):
        """
        raised when a getting a Model fails
        """
        self.message = message
        super().__init__(self.message)


class ModelCreationError(Exception):
    def __init__(self, message: str = "Could not add model"):
        """
        raised when a model creation fails
        """
        self.message = message
        super().__init__(self.message)


class ModelUpdateError(Exception):
    def __init__(self, message: str = "Could not update model"):
        """
        raised when a model update fails
        """
        self.message = message
        super().__init__(self.message)


class WorkspaceFetchDataError(Exception):
    def __init__(self, message: str = "Unable to get workspaces"):
        """
        raised when failed fetching workspaces data
        """
        self.message = message
        super().__init__(self.message)


class WorkspaceAlreadyExist(Exception):
    def __init__(self, message: str = "WorkspaceDto with the same name already exists"):
        """
        raised when a workspace with same name already exist
        """
        self.message = message
        super().__init__(self.message)


class WorkspaceCreationError(Exception):
    def __init__(self, message: str = "workspace already exist"):
        """
        raised when a workspace already exist
        """
        self.message = message
        super().__init__(self.message)


class WorkspaceNotFoundError(Exception):
    def __init__(self, message: str = "workspace not found"):
        """
        raised when a workspace is not found
        """
        self.message = message
        super().__init__(self.message)


class DuplicateAssignmentError(Exception):
    def __init__(self, message: str = "assignment already exist"):
        """
        raised when there are same workspace assignment for user
        """
        self.message = message
        super().__init__(self.message)
