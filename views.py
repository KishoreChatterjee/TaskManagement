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
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        

        if not username or not email or not password:
            return JsonResponse({
                "error": "Input fields should not be empty"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(email=email, username=username, password=password)
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
        username = data.get('username')
        password = data.get('password')

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
        if request.user=="":
            
            raise Exception("user is not signed in")
        else:
            user=request.user
            try:
                boardName= (json.loads(request.body))["bname"]
                description=(json.loads(request.body))["desc"]
                if boardName == "" or description =="":
                    raise Exception("Board name and des not provided check once")
                checkBoardname = Boards.objects.filter(boardName=boardName).exists()
                if checkBoardname == True:
                    raise Exception("Board name alredy added to the database")
                else:
                    newBoard=Boards.objects.create(boardName=boardName,description=description,user=user)
                    return JsonResponse({
                        "boardId":newBoard.id,
                        "message":"board created sucessfully"
                    })
            except Exception as ex:
                return JsonResponse({
                    "massage":str(ex),
                    "status":"filed"
                },status = status.HTTP_409_CONFLICT)
    except Exception as ex:
        return JsonResponse({
            "massage":str(ex),
            "status":"filed"
        },status = status.HTTP_401_UNAUTHORIZED)
          
# @api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])
# def createList(request):
#     try:
#         if request.user=="":
#             raise Exception("user is not signed in")
#         else:
#             user=request.user
#             try:
#                 listtitle= (json.loads(request.body))["Lname"]
#                 board_id=(json.loads(request.body))["BoardId"]
#                 board_instance = User.objects.get(id=board_id)
#                 if listtitle == "" or board_id =="":
#                     raise Exception("Card name and des not provided check once")
#                 checkCardname = List.objects.filter(board=board_instance,listTitle=listtitle).exists()
#                 if checkCardname == True:
#                     raise Exception("Card alredy added to the database")
#                 else:
#                     newList=List.objects.create(listTitle=listtitle,board=board_instance)
#                     return JsonResponse({
#                         "listTitle":newList.listTitle,
#                         "message":"list created sucessfully"
#                     })
#             except Exception as ex:
#                 return JsonResponse({
#                     "massage":str(ex),
#                     "status":"filed"
#                 },status = status.HTTP_409_CONFLICT)
#     except Exception as ex:
#         return JsonResponse({
#             "massage":str(ex),
#             "status":"filed"
#         },status = status.HTTP_401_UNAUTHORIZED)

        
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def createCard(request):
    try:
        if request.user=="":
            raise Exception("user is not signed in")
        else:
            user=request.user
            try:
                cardTitle= (json.loads(request.body))["Cname"]
                cardDescription=(json.loads(request.body))["Desc"]
                boardId=(json.loads(request.body))['board']
                board_instance = User.objects.get(id=boardId)
                if cardTitle == "" :
                    raise Exception("Card name not provided check once")
                checkCardname = Card.objects.filter(cardTitle=cardTitle,board=board_instance).exists()
                if checkCardname == True:
                    raise Exception("Card alredy added to the database")
                else:
                    newCard=Card.objects.create(cardTitle=cardTitle,cardDescription=cardDescription,board=board_instance)
                    return JsonResponse({
                        "cardTitle":newCard.cardTitle,
                        "message":"card created sucessfully"
                    })
            except Exception as ex:
                return JsonResponse({
                    "massage":str(ex),
                    "status":"filed"
                },status = status.HTTP_409_CONFLICT)
    except Exception as ex:
        return JsonResponse({
            "massage":str(ex),
            "status":"filed"
        },status = status.HTTP_401_UNAUTHORIZED)
        
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def createList(request):
    try:
        if not request.user.is_authenticated:
            raise Exception("User is not signed in")
        else:
            user = request.user
            data = json.loads(request.body)
            listTitle = data["listTitle"]
            board_id = data["board_id"]
            card_id = data.get("card_id")
            todo_items = data.get("todo_items", [])

            # Check if the board_id is valid
            if not Boards.objects.filter(id=board_id, user=user).exists():
                raise Exception("Board not found for the current user")

            # Check if the card_id is valid (if provided)
            if card_id and not Card.objects.filter(id=card_id, board_id=board_id).exists():
                raise Exception("Card not found for the specified board")

            # Create the list
            new_list = List.objects.create(listTitle=listTitle, board_id=board_id, card_id=card_id)

            # Create todo items associated with the list
            for itemTitle in todo_items:
                TodoItem.objects.create(itemTitle=itemTitle, list=new_list, card_id=card_id)

            return JsonResponse({
                'message': 'List created successfully',
                'listTitle': new_list.listTitle,
                'board_id': new_list.board_id,
                'card_id': new_list.card_id,
                'todo_items': [item.itemTitle for item in new_list.todoitem_set.all()],
            })

    except Exception as ex:
        return JsonResponse({
            "message": str(ex),
            "status": "failed"
        }, status=status.HTTP_409_CONFLICT)
    except:
        return JsonResponse({
            "message": "Unauthorized",
            "status": "failed"
        }, status=status.HTTP_401_UNAUTHORIZED)




