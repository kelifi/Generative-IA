from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

middlewares = [Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"])]
