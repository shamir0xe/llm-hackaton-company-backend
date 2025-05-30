from enum import Enum


class ExceptionTypes(Enum):
    CONNECTION_INVALID = "connection_invalid"
    DATABASE_INVALID = "database_invalid"
    ID_INVALID = "id_invalid"
    TIME_FORMAT_NOT_SUPPORTED = "time_format_not_supported"
    TRIE_TREE_INVALID = "trie_tree_invalid"
    DB_SESSION_NOT_AVAILABLE = "db_session_not_available"
    DB_SESSION_NOT_FOUND = "db_session_not_found"
    USER_ID_INVALID = "user_id_invalid"
    SMS_CODE_MISSING = "sms_code_missing"
    SMS_TYPE_INVALID = "sms_type_invalid"
    SMS_PHONE_NUMBER_INVALID = "sms_phone_number_invalid"
    SMS_SEND_FAILED = "sms_send_failed"
    TOKEN_INVALID = "token_invalid"
    IMAGE_INVALID = "image_invalid"
    INTERNAL_ERROR = "internal_error"
