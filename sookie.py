# -*- coding: utf-8 -*-

from flask import Flask, url_for, render_template, redirect, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from wtforms import TextField, validators
from wtforms.ext.sqlalchemy.fields import QuerySelectField

try:
    from config import SQLALCHEMY_DATABASE_URI
except ImportError:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    source = db.Column(db.String(120), unique=True)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
                               backref=db.backref('recipe',
                                                  lazy='dynamic'))

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


class RecipeForm(Form):
    name = TextField('Name', [validators.Required(),
                              validators.Length(min=4, max=80)])
    source = TextField('Source', [validators.Required(),
                                  validators.Length(min=6, max=35)])
    category = QuerySelectField(query_factory=lambda: Category.query.all())


@app.route('/recipe/<int:id>')
def show_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    cat = recipe.category
    return render_template('recipe.html',
                           recipe=recipe,
                           category_link=url_for('show_category', id=cat.id),
                           category=cat.name)


@app.route('/')
def list_recipes():
    return render_template('start.html', categories=Category.query.all())


@app.route('/categories')
@app.route('/category/')
def list_categories():
    return render_template('categories.html', categories=Category.query.all())


@app.route('/category/<int:id>')
def show_category(id):
    category = Category.query.filter_by(id=id).first_or_404()
    return render_template('category_overview.html',
                           category=category,
                           recipes=sorted(Recipe.query.filter_by(category_id=id).all(),
                                          key=lambda r: r.name.lower()))


@app.route('/recipe/new', methods=('GET', 'POST'))
def submit_recipe():
    form = RecipeForm(request.form, csrf_enabled=False)

    if form.validate_on_submit():
        rec = Recipe(form.name.data, form.source.data, form.category.data)
        db.session.add(rec)
        db.session.commit()

        return redirect(url_for('show_recipe', id=rec.id))

    return render_template('new_recipe.html', form=form, errors=form.errors)


@app.errorhandler(404)
def error_occured(error):
    return render_template('404.html', error=error), 404


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
    except Exception as error:
        print("Failed to load example data: {}".format(error))

    app.run(debug=True)
