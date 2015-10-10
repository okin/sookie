#! python3
# -*- coding: utf-8 -*-

# sookie is a recipe and food planning web application
# Copyright (C) 2015  Niko Wenselowski

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from flask import Flask, g, redirect, render_template, request, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from wtforms import TextField, validators
from wtforms.ext.sqlalchemy.fields import QuerySelectField

app = Flask(__name__)
app.config.from_object("config")
app.config.from_envvar('SOOKIE_SETTINGS', silent=True)
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
        return '<Recipe({!r}, {!r})>'.format(self.name, self.source)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Category({!r})>'.format(self.name)


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
    recipes = sorted(Recipe.query.filter_by(category_id=id).all(),
                     key=lambda recipe: recipe.name.lower())
    return render_template('category_overview.html',
                           category=category,
                           recipes=recipes,
                           )


@app.route('/recipe/new', methods=('GET', 'POST'))
def submit_recipe():
    form = RecipeForm(request.form)

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
