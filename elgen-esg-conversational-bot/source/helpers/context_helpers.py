from contextvars import ContextVar

# Create a context variable to store the user_id
user_id_var = ContextVar("user_id")