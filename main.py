import json
import traceback
from typing import Optional
from bson import ObjectId
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pydantic import BaseModel


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


app = Flask(__name__)

app.config["MONGO_URI"] = ""
app.json_encoder = JSONEncoder

mongo = PyMongo(app)
menuCol = mongo.db.menu


class MenuItem(BaseModel):
    name: str
    type: str
    veg: bool
    discount: int = 0


class UpdateMenuItem(MenuItem):
    name: Optional[str]
    type: Optional[str]
    veg: Optional[bool]
    discount: Optional[int] = 0


@app.route("/menu", methods=['GET', 'POST', 'PATCH', 'DELETE'])
def menu():
    if request.method == 'GET':
        try:
            page = request.args.get('page', type=int, default=0)
            veg = request.args.get('veg', type=int, default=None)  # to filter.

            page_size = 2
            multiplier = (page - 1) * page_size  # 2 at a time

            if page == 0:
                multiplier = 0
                page_size = 0

            if veg is None:
                data = list(menuCol.find({}).skip(multiplier).limit(page_size))
                return jsonify(ok=True, data=data), 200
            elif veg is not None:
                data = list(menuCol.find({"veg": bool(veg)}).skip(multiplier).limit(page_size))
                return jsonify(ok=True, data=data), 200

        except:
            traceback.print_exc()
            return jsonify(ok=False, message="something went wrong!"), 400

    elif request.method == "POST":
        try:
            data = request.get_json()
            item = MenuItem(**data)
            menuCol.insert_one({"name": item.name,
                                "type": item.type,
                                "veg": item.veg,
                                "discount": item.discount
                                })
            return jsonify(ok=True, message="inserted!"), 200
        except:
            return jsonify(ok=False, message="something went wrong!"), 400

    elif request.method == "PATCH":
        try:
            data = request.get_json()
            id = data.pop("id")
            item = UpdateMenuItem(**data) #just to validate
            menuCol.update_one({"_id": ObjectId(id)}, {"$set": data})
            return jsonify(ok=True, message="updatwd!"), 200
        except:
            traceback.print_exc()
            return jsonify(ok=False, message="something went wrong!"), 400

    elif request.method == "DELETE":
        try:
            data = request.get_json(force=True)
            id = data['id']
            menuCol.delete_one({'_id': ObjectId(id)})
            return jsonify(ok=True, message="Deleted!"), 200

        except:
            return jsonify(ok=False, message="something went wrong!"), 400


if __name__ == '__main__':
    app.run()
