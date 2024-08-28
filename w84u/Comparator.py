from .models import Session, CustomUser , MaybeMatch


def create_maybematch(user_1,session_1,user_2, session_2):

    match = MaybeMatch.objects.create(
       user_1=user_1,
       session_1=session_1,
        user_2=user_2,
        session_2=session_2
    )
