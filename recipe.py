# -*- coding: utf-8 -*-

from flask import Flask, url_for, render_template, redirect, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from wtforms import TextField, validators
from wtforms.ext.sqlalchemy.fields import QuerySelectField
app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    source = db.Column(db.String(120), unique=True)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
        backref=db.backref('recipe', lazy='dynamic'))

    def __init__(self, name, source, category):
        self.name = name
        self.source = source
        self.category = category

    def __repr__(self):
        return '<Recipe({}, {})>'.format(self.name, self.source)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Category %r>' % self.name


def enabled_categories():
    return Category.query.all()


class RecipeForm(Form):
    name = TextField('Name', [validators.Required(), validators.Length(min=4, max=80)])
    source = TextField('Source', [validators.Required(), validators.Length(min=6, max=35)])
    category = QuerySelectField(query_factory=enabled_categories)


@app.route('/recipe/<int:id>')
def showRecipe(id):
    return '{r.name}: {r.source}'.format(r=Recipe.query.get(id))


@app.route('/')
def listRecipes():
    return render_template('start.html', categories=Category.query.all())


@app.route('/categories')
@app.route('/category/')
def listCategories():
    cats = []
    for cat in Category.query.all():
        cats.append('<li><a href="{url}">{name}</a></li>'.format(name=cat.name, url=url_for('showCategory', id=cat.id)))

    return ''.join(cats)

@app.route('/category/<int:id>')
def showCategory(id):
    category = Category.query.filter_by(id=id).one()
    return render_template('category_overview.html', category=category, recipes=Recipe.query.filter_by(category_id=id).all())


@app.route('/recipe/new', methods=('GET', 'POST'))
def submitRecipe():
    form = RecipeForm(request.form, csrf_enabled=False)

    if form.validate_on_submit():
        rec = Recipe(form.name.data, form.source.data, form.category.data)
        db.session.add(rec)
        db.session.commit()

        return redirect('/')

    return render_template('new_recipe.html', form=form, errors=form.errors)

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
