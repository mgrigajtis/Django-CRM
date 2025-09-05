from django.urls import path

from lender import views

app_name = "lender"

urlpatterns = [
    path("", views.LenderListView.as_view()),
    path("<str:pk>/", views.LenderDetailView.as_view())
]
