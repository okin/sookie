# -*- coding: utf-8 -*-

from flask import Flask, url_for 
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    origin = db.Column(db.String(120), unique=True)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
        backref=db.backref('recipe', lazy='dynamic'))

    def __init__(self, name, origin, category):
        self.name = name
        self.origin = origin
        self.category = category

    def __repr__(self):
        return '<Recipe({}, {})>'.format(self.name, self.origin)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Category %r>' % self.name


@app.route('/recipe/<int:id>')
def showRecipe(id):
    return '{r.name}: {r.origin}'.format(r=Recipe.query.get(id))


@app.route('/')
def listRecipes():
    overview = []
    for recipe in Recipe.query.all():
        overview.append('<li><a href="{url}">{name}</a></li>'.format(name=recipe.name, url=url_for('showRecipe', id=recipe.id)))

    return ''.join(overview) 

@app.route('/categories')
def listCategories():
    cats = []
    for cat in Category.query.all():
        cats.append('<li><a href="{url}">{name}</a></li>'.format(name=cat.name, url=url_for('showCategory', id=cat.id)))

    return ''.join(cats)

@app.route('/category/<int:id>')
def showCategory(id):
    overview = []
    for recipe in Recipe.query.filter_by(category_id=id).all():
        overview.append('<li><a href="{url}">{name}</a></li>'.format(name=recipe.name, url=url_for('showRecipe', id=recipe.id)))

    return ''.join(overview) 
    

if __name__ == "__main__":
    db.create_all()

    breakfast = Category('Frühstück')
    lunch = Category('Mittagessen')
    dinner = Category('Abendessen')
    
    try:
        db.session.add(breakfast)
        db.session.add(lunch)
        db.session.add(dinner)
        db.session.add(Recipe('Mandelfoo', 'VFF, S.123', breakfast))
        db.session.add(Recipe('Foobrot', 'VFF, S.124', lunch))
        db.session.add(Recipe('Banane', 'VFF, S.125', breakfast))
        db.session.commit()
    except Exception as e:
        print(e)

    app.run(debug=True)
