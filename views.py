from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import *
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics,status,views,permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "Method not supported",
            "status": "Failed"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    try:
        data = json.loads(request.body)
        email = data['email']
        username = data['username']
        password = data['password']
        orgName = data['organisationName'] if data['organisationName'] else ''
        

        if not username or not email or not password:
            return JsonResponse({
                "error": "Input fields should not be empty"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(email=email, username=username, password=password,organisationName=orgName)
        user.save()
        
        send_mail(
            "Congratualations",
            "We are so happy to have you onboard.",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return JsonResponse({
            "message": f"User {username} registered successfully"
        }, status=status.HTTP_201_CREATED)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "Method not supported",
            "status": "Failed"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    try:
        data = json.loads(request.body)
        username = data['username']
        password = data['password']

        if not username or not password:
            return JsonResponse({
                "error": "Input fields should not be empty"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)

            return JsonResponse({
                "access-token": str(refresh.access_token),
                "refresh-token": str(refresh)

            })
        else:
            return JsonResponse({
                "error": "Invalid username or password."
            }, status=status.HTTP_401_UNAUTHORIZED)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)
                
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def createBoard(request):
    try:
        if request.user.organisationName == '':
            return JsonResponse({
                "status":"failed",
                "message":"You need to be owner or a member of an oranisation"
            })
        
        user = request.user
        data = json.loads(request.body)
        boardName = data['boardName']
        description = data['description']

        if not boardName or not description:
            return JsonResponse({
                "error": "Board name and description are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        new_board = Board.objects.create(boardName=boardName, description=description, user=user)
        return JsonResponse({
            "boardId": new_board.id,
            "message": "Board created successfully"
        }, status=status.HTTP_201_CREATED)

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def createListTitle(request):
    try:
        user = request.user
        data = json.loads(request.body)
        listTitle = data['listTitle']
        cardId = data['cardId']

        card_instance = Card.objects.get(id=cardId)

        if not listTitle or not card_instance:
            return JsonResponse({
                "error": "List title and valid card ID are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        new_list = List.objects.create(listTitle=listTitle, card=card_instance)
        return JsonResponse({
            "listId": new_list.id,
            "message": "List title created successfully"
        }, status=status.HTTP_201_CREATED)

    except Card.DoesNotExist:
        return JsonResponse({
            "error": "Card does not exist."
        }, status=status.HTTP_404_NOT_FOUND)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def createCard(request):
    try:
        user = request.user
        data = json.loads(request.body)
        cardTitle = data['cardTitle']
        cardDescription = data['cardDescription']
        boardId = data['boardId']

        board_instance = Board.objects.get(id=boardId)

        if not cardTitle or not board_instance:
            return JsonResponse({
                "error": "Card title and valid board ID are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        new_card = Card.objects.create(cardTitle=cardTitle, cardDescription=cardDescription, board=board_instance)
        return JsonResponse({
            "cardId": new_card.id,
            "message": "Card created successfully"
        }, status=status.HTTP_201_CREATED)

    except Board.DoesNotExist:
        return JsonResponse({
            "error": "Board does not exist."
        }, status=status.HTTP_404_NOT_FOUND)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def createTask(request):
    try:
        user = request.user
        data = json.loads(request.body)
        list_id = data['list_id']
        to_do_task = data['toDoTasks']
        card_status = data['card_status']

        list_instance = List.objects.get(id=list_id)

        if not to_do_task or not list_instance:
            return JsonResponse({
                "error": "Task description and valid list ID are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the card_status is valid
        if card_status not in ['assigned', 'toDo', 'done']:
            return JsonResponse({
                "error": "Invalid card_status. It should be one of 'assigned', 'toDo', or 'done'."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create the task
        new_task = Task(
            toDoTasks=to_do_task,
            list=list_instance,
            isActive=True  # Assuming tasks are active by default
        )

        new_task.save()

        # Update the card status
        list_instance.card.cardStatus = card_status
        list_instance.card.save()

        return JsonResponse({
            "taskId": new_task.id,
            "message": "Task created successfully",
            "card_status": card_status
        }, status=status.HTTP_201_CREATED)

    except List.DoesNotExist:
        return JsonResponse({
            "error": "List does not exist."
        }, status=status.HTTP_404_NOT_FOUND)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def addPersonToOranistation(request):
    emaill=(json.loads(request.body))['email']
    organisationName = request.user.organisationName
    if organisationName== "" :
        raise Exception("your organisation is not registered")
    else:
        user_instance = User.objects.get(email=emaill)
        if not user_instance:
            return JsonResponse({
                "message" : "user not found"
            })
        else:
            user_instance.organisationName=organisationName
            user_instance.save()
            
            return JsonResponse({
                    "message" :f"{user_instance} is added to the organisation successfully"
                })
            
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def addPersonToBoard(request):
    # Check if the user has an organization
    if not request.user.organisationName:
        return JsonResponse({
            "status": "failed",
            "message": "Unauthorized access. User does not belong to any organization."
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        data = json.loads(request.body)
        email = data['email']
        board_id = data['boardId']

        user_instance = User.objects.get(email=email)
        board_instance = Board.objects.get(id=board_id)

        if not user_instance:
            return JsonResponse({
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the user belongs to the same organization as the board owner
        if user_instance.organisationName != request.user.organisationName:
            return JsonResponse({
                "status": "failed",
                "message": "User does not belong to the same organization as the board owner."
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the user is already associated with the board
        if board_instance.user == user_instance:
            return JsonResponse({
                "message": "User is already associated with the board."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update the board's user field to the new user
        addingUserToBoard = Board.objects.create(boardName = board_instance.boardName, description = board_instance.description,user_id = user_instance.id)
        addingUserToBoard.save()

        return JsonResponse({
            "message": f"User {user_instance.username} added to the board successfully."
        }, status=status.HTTP_200_OK)

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return JsonResponse({
            "error": "User does not exist."
        }, status=status.HTTP_404_NOT_FOUND)
    except Board.DoesNotExist:
        return JsonResponse({
            "error": "Board does not exist."
        }, status=status.HTTP_404_NOT_FOUND)
    
    
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def addUserToCard(request):
    try:
        data = json.loads(request.body)
        email = data['email']
        card_id = data['cardId']

        user_instance = User.objects.get(email=email)
        card_instance = Card.objects.get(id=card_id)

        if not user_instance:
            return JsonResponse({
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the user belongs to the same organization as the card owner
        if user_instance.organisationName != request.user.organisationName:
            return JsonResponse({
                "status": "failed",
                "message": "User does not belong to the same organization as the card owner."
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the user is already associated with the card
        if user_instance in card_instance.users.all():
            return JsonResponse({
                "message": f"User {user_instance.username} is already associated with the card."
            }, status=status.HTTP_200_OK)

        # Add the user to the card
        card_instance.users.add(user_instance)
        card_instance.save()

        # Ensure the added user is associated with the same card as the request user
        user_instance.card_set.add(card_instance)

        return JsonResponse({
            "message": f"User {user_instance.username} added to the card {card_instance.id} successfully."
        }, status=status.HTTP_200_OK)

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return JsonResponse({
            "error": "User does not exist."
        }, status=status.HTTP_404_NOT_FOUND)
    except Card.DoesNotExist:
        return JsonResponse({
            "error": "Card does not exist."
        }, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def removeUserFromOrganisation(request):
    try:
        data = json.loads(request.body)
        email = data['email']

        user_instance = User.objects.get(email=email)

        if not user_instance:
            return JsonResponse({
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the user belongs to the same organization
        if user_instance.organisationName != request.user.organisationName:
            return JsonResponse({
                "status": "failed",
                "message": "User does not belong to the same organization."
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Set isActive to False
        user_instance.isActive = False
        user_instance.save()

        return JsonResponse({
            "message": f"User {user_instance.username} removed from the organisation successfully."
        }, status=status.HTTP_200_OK)

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return JsonResponse({
            "error": "User does not exist."
        }, status=status.HTTP_404_NOT_FOUND)
    
   
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def updateBoardName(request):
    try:
        data = json.loads(request.body)
        board_id = data['boardId']
        new_board_name = data['newBoardName']

        board_instance = Board.objects.get(id=board_id)

        if not board_instance:
            return JsonResponse({
                "error": "Board does not exist."
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is the owner of the board
        if board_instance.user != request.user:
            return JsonResponse({
                "status": "failed",
                "message": "User is not the owner of the board."
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Update the name of the board
        board_instance.boardName = new_board_name
        board_instance.save()

        return JsonResponse({
            "message": "Board name updated successfully."
        }, status=status.HTTP_200_OK)

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)
    except Board.DoesNotExist:
        return JsonResponse({
            "error": "Board does not exist."
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def removeBoard(request):
    try:
        data = json.loads(request.body)
        board_id = data['boardId']

        board_instance = Board.objects.get(id=board_id)

        if not board_instance:
            return JsonResponse({
                "error": "Board does not exist."
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is the owner of the board
        if board_instance.user != request.user:
            return JsonResponse({
                "status": "failed",
                "message": "User is not the owner of the board."
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Remove the board
        board_instance.delete()

        return JsonResponse({
            "message": "Board removed successfully."
        }, status=status.HTTP_200_OK)

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)
    except Board.DoesNotExist:
        return JsonResponse({
            "error": "Board does not exist."
        }, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def makeCardInactive(request):
    try:
        data = json.loads(request.body)
        card_id = data['cardId']

        card_instance = Card.objects.get(id=card_id)

        if not card_instance:
            return JsonResponse({
                "error": "Card does not exist."
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is the owner of the board
        if card_instance.board.user != request.user:
            return JsonResponse({
                "status": "failed",
                "message": "User is not the owner of the card's board."
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Set the card as inactive
        card_instance.isActive = False
        card_instance.save()

        return JsonResponse({
            "message": "Card set as inactive successfully."
        }, status=status.HTTP_200_OK)

    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)
    except Card.DoesNotExist:
        return JsonResponse({
            "error": "Card does not exist."
        }, status=status.HTTP_404_NOT_FOUND)

