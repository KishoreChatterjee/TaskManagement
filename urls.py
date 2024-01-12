from django.urls import path
from .views import *

urlpatterns = [
    path('register/', register),
    path('login/', login),
    path("createBoard/", createBoard),
    path('createCard/', createCard),
    path('createListTitle/', createListTitle),
    path('tasks/', createTask),
    path('addPersonToOranistation/',addPersonToOranistation),
    path('addPersonToBoard/',addPersonToBoard),
    path('addUserToCard/',addUserToCard),
    path('removeUserFromOrganisation/',removeUserFromOrganisation),
    path('updateBoardName/',updateBoardName),
    path('removeBoard/',removeBoard),
    path('makeCardInactive/',makeCardInactive),
]
