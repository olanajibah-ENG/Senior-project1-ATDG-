from .project_views import ProjectListCreateAPIView,ProjectRetrieveUpdateDestroyAPIView
from .user_views import UserRegistrationAPIView, UserLoginAPIView    # ⬅️ تمت الإضافة
from .artifact_views import ArtifactListCreateAPIView, ArtifactRetrieveUpdateDestroyAPIView
from .account_views import (
    AdminUserListView,
    AdminCreateReviewerView,
    AdminToggleUserActiveView,
    ChangePasswordView,
    OnlineUsersView,
)
from .reviewer_views import ReviewerNotifyAdminView