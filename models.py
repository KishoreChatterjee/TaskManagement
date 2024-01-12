from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True)
    organisationName = models.CharField(max_length = 40)
    isAdmin = models.BooleanField(default = False)
    def __str__(self):
        return self.username
    
class Board(models.Model):
    boardName = models.CharField(max_length=20)
    description = models.TextField(max_length=100000)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.boardName

class Card(models.Model):
    cardTitle = models.CharField(max_length=200)
    cardDescription = models.TextField()
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    users = models.ManyToManyField(User)  # Adding this line

    def __str__(self):
        return self.cardTitle

class List(models.Model):
    listTitle = models.CharField(max_length=200)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)

    def __str__(self):
        return self.listTitle

class Task(models.Model):
    toDoTasks = models.CharField(max_length=200)
    list = models.ForeignKey(List, on_delete=models.CASCADE)
    isActive = models.BooleanField()

    def __str__(self):
        return self.toDoTasks
