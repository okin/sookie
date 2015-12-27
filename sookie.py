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

from flask import Flask, redirect, render_template, request, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms import TextField, validators
from wtforms.fields.html5 import DateField
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField

app = Flask(__name__)
app.config.from_object("config")
app.config.from_envvar('SOOKIE_SETTINGS', silent=True)
db = SQLAlchemy(app)
admin = Admin(app, name='sookie', template_mode='bootstrap3')


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name=None):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Category({!r})>'.format(self.name)


class PlannableItem(db.Model):
    __tablename__ = 'plannableitem'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    type = db.Column(db.String(10))

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'plannableitem',
        'with_polymorphic': '*'
    }

    def __init__(self, name=""):
        self.name = name

    def __repr__(self):
        return '<PlannableItem({!r})>'.format(self.name)


class Recipe(PlannableItem):
    __tablename__ = 'recipe'
    id = db.Column(db.Integer, db.ForeignKey('plannableitem.id'), primary_key=True)
    source = db.Column(db.String(120), unique=True)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
                               backref=db.backref('recipe',
                                                  lazy='dynamic'))

    __mapper_args__ = {'polymorphic_identity': 'recipe'}

    def __init__(self, name="", source=None, category=None):
        self.name = name
        self.source = source
        self.category = category

    def __repr__(self):
        return '<Recipe({!r}, {!r})>'.format(self.name, self.source)


class RecipeForm(Form):
    name = TextField('Name', [validators.Required(),
                              validators.Length(min=4, max=80)])
    source = TextField('Source', [validators.Required(),
                                  validators.Length(min=6, max=35)])
    category = QuerySelectField(query_factory=lambda: Category.query.all())


day_recipe_mapping = db.Table('day_recipe_mapping', db.metadata,
    db.Column('day_id', db.Integer, db.ForeignKey('day.id')),
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'))
)


class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    recipes = db.relationship('Recipe', secondary=day_recipe_mapping)

    def __init__(self, date, recipes=None):
        self.date = date
        self.recipes = recipes or []

    def __repr__(self):
        return '<Day({!r}, {!r})>'.format(self.date, self.recipes)


class DayForm(Form):
    date = DateField('Date', format='%d.%m.%Y',
                             validators=[validators.required()]
                             )
    recipes = QuerySelectMultipleField(query_factory=lambda: Recipe.query.all())


def init_db():
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


@app.route('/day/')
def list_days():
    return render_template('day_overview.html', days=Day.query.all())


@app.route('/day/<int:id>')
def show_day(id):
    day = Day.query.filter_by(id=id).first_or_404()
    return render_template('day.html', day=day)


@app.route('/day/<int:id>/edit', methods=('GET', 'POST'))
def edit_day(id):
    day = Day.query.filter_by(id=id).first_or_404()
    form = DayForm(request.form, day)

    if form.validate_on_submit():
        day.recipes = form.recipes.data
        db.session.add(day)
        db.session.commit()

        return redirect(url_for('show_day', id=day.id))

    return render_template('edit_day.html', day=day, form=form)


@app.route('/day/new', methods=('GET', 'POST'))
def add_day():
    form = DayForm(request.form)

    if form.validate_on_submit():
        day = Day(form.date.data, form.recipes.data)
        db.session.add(day)
        db.session.commit()

        return redirect(url_for('show_day', id=day.id))

    return render_template('new_day.html', form=form, errors=form.errors)


@app.errorhandler(404)
def error_occured(error):
    return render_template('404.html', error=error), 404


class CategoryModelView(ModelView):
    create_modal = True
    edit_modal = True
    form_excluded_columns = ['recipe']


class DayModelView(ModelView):
    create_modal = True
    edit_modal = True
    form_excluded_columns = ['recipe']


admin.add_view(ModelView(Recipe, db.session))
admin.add_view(CategoryModelView(Category, db.session))
admin.add_view(DayModelView(Day, db.session))

if __name__ == "__main__":
    init_db()

    app.run(debug=True)
