from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    DocumentProcessingException,
    VectorStoreException
)

from app.core.logger import logger


async def document_exception_handler(
    request: Request,
    exc: DocumentProcessingException
):

    logger.exception(exc.message)

    return JSONResponse(

        status_code=500,

        content={

            "detail": exc.message

        }

    )


async def vector_exception_handler(
    request: Request,
    exc: VectorStoreException
):

    logger.exception(exc.message)

    return JSONResponse(

        status_code=500,

        content={

            "detail": exc.message

        }

    )