from rest_framework.views import APIView
from rest_framework.response import Response
from .open_ai import Request as OpenAIRequest
from youtubesearchpython import VideosSearch
from .models import Food, Ingredient
import logging
import traceback
from threading import Thread

logger = logging.getLogger('django')


class ListFoods(APIView):
    """
    The class handles User request to send a request to 3rd libraries
    """

    def get(self, request, *args, **kwargs):
        """
        the function takes post request and proceeds for OPENAI
        :param request: request data
        :return:  Response of status
        """

        try:
            ingredients = self.request.data.get("ingredients")

            if ingredients:
                ingredients = " ,".join(ingredients)
                openai_req = OpenAIRequest()
                open_res = openai_req.get_list_food(ingredients).replace("\n", "")
                filtered = ''.join(filter(lambda c: not c.isdigit(), open_res))
                list_of_foods = filtered.split(".")
                list_of_foods = [i for i in list_of_foods if i]

                return Response({
                    "Ready Response": list_of_foods
                })
            else:
                return Response({
                    "message": "error, send ingredients with same key",
                })
        except BaseException as e:
            err = traceback.format_exc()
            logger.error(err)


class DetailFood(APIView):
    """
    The class handles User request to send a request to 3rd libraries
    """

    def get_food(self, food_name):
        """
        :param food_name: str, contains food name
        :return: return food if exists
        """
        try:
            food = Food.objects.get(name__iexact=food_name)
            if food:
                return food

        except BaseException as e:
            err = traceback.format_exc()
            logger.error(err)

    def create_food(self, food_name, link, recipe, ingredients):
        """
        :param food_name: str, contains food name
        :param link: str, YouTube link of food
        :param recipe: str, description how to coook
        :param ingredients: list, list of ingredients
        :return: True if created
        """
        try:
            ing_ids = []
            for i in ingredients:
                ins = Ingredient.objects.get_or_create(name=i)
                print(ins)
                ing_ids.append(ins)
            food = Food.objects.create(name=food_name, youtube_link=link, recipe=recipe)
            food.main_ingredients.add(*ing_ids)  # adds all together
            logger.info("created")
            return True
        except BaseException as e:
            err = traceback.format_exc()
            logger.error(err)

    def get(self, request, *args, **kwargs):
        """
        the function takes post request and proceeds for OPENAI and YouTube API
        :param request: request data
        :return:  Response of status
        """
        try:
            food_name = self.request.data.get("name")
            ingredients = self.request.data.get("ingredients")

            if food_name and ingredients:
                ingredients = [i.strip() for i in ingredients]
                food_name = food_name.strip()

                food_exists = self.get_food(food_name)

                ready_response = []

                if food_exists:
                    ready_response.append({
                        "Name": food_name,
                        "link": food_exists.youtube_link,
                        "recipe": food_exists.recipe
                    })
                else:
                    openai_req = OpenAIRequest()

                    response_youtube = VideosSearch(food_name, limit=1).result().get("result")[0].get("link")

                    recipe = openai_req.get_recipe(food_name, ingredients)
                    ready_response.append({"Name": food_name, "link": response_youtube, "recipe": recipe})
                    t = Thread(target=self.create_food, args=[food_name, response_youtube, recipe,ingredients ])
                    t.run()

                return Response({
                    "Ready Response": ready_response
                })
            else:
                return Response({
                    "message": "error, send ingredients with same key",
                })
        except BaseException as e:
            err = traceback.format_exc()
            logger.error(err)
