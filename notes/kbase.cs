

//ref https://www.index.dev/blog/how-to-set-global-variables-python
//ref: https://dev.to/igorbenav/fastapi-mistakes-that-kill-your-performance-2b8k


//---------------------------------------------------
# Good - Dataclass for internal processing
@dataclass
class UserInternal:
    name: str
    email: str
    age: int
    created_at: datetime
    processed: bool = False

@app.post("/users")
async def create_user(user_request: UserRequest):
    # Pydantic validates the incoming request

    # Convert to internal dataclass for processing
    user = UserInternal(
        name=user_request.name,
        email=user_request.email,
        age=user_request.age,
        created_at=datetime.utcnow()
    )

    # Do internal processing with lightweight dataclass
    process_user(user)

    return {"id": user.id}
//---------------------------------------------------
