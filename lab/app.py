from flask import Flask, render_template, request
from neo4j import GraphDatabase
from flask_paginate import Pagination
import os

app = Flask(__name__)

MOVIE_IMG = os.path.join('static', 'movies')

app.config['UPLOAD_FOLDER'] = MOVIE_IMG

### user start ###
@app.context_processor
def inject_data():
    con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
    cur = con.session()
    latest = cur.run('''
                MATCH (p:Person)-[r]->(m:Movie)

RETURN distinct
  CASE
    WHEN type(r) = "ACTED_IN" THEN "Жүжигчин"
    WHEN type(r) = "DIRECTED" THEN "Найруулагч"
    WHEN type(r) = "FOLLOWS" THEN "Дагагч"
    WHEN type(r) = "PRODUCED" THEN "Продюсер"
    WHEN type(r) = "WROTE" THEN "Зохиолч"
    ELSE "Тоймч"
  END AS turul
''')
    return {'neo4j_data': latest} 

@app.route("/")
def index():
    con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
    cur = con.session()
    latest = cur.run("match(m:Movie) return  m.title as title, m.released as released, m.image as image, id(m) as movieID ORDER BY id(m) DESC LIMIT 8")
    return render_template('user/index.html', utga=latest)

@app.route("/movies", methods = ['GET', 'POST'])
def movies(limit=9):
    if request.method == 'GET':
        page = int(request.args.get("page",1))
        start = (page-1) * limit
        con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = con.session()
        movies = cur.run("match(m:Movie) return  m.title as title, m.released as released, m.image as image")
        latest = list(movies)
        too = len(latest)
        paginate = Pagination(page=page, per_page=limit, total=too)
        paged_movies = cur.run("match(m:Movie) return  m.title as title, m.released as released, m.image as image, id(m) as movieID SKIP $skip LIMIT $limit", skip=start, limit=limit)
        return render_template('user/movies.html', utga=paged_movies, too=too, paginate=paginate)
    elif request.method == 'POST':
        mname = request.form['txtMovieTitle']
        min_released = request.form.get('minReleased')
        max_released = request.form.get('maxReleased')
        con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = con.session()
        search_movie = list(cur.run('''
        MATCH (m:Movie)
        WHERE toLower(m.title) CONTAINS toLower($title)
        RETURN m.title AS title, m.released AS released, m.image AS image, id(m) AS movieID
''', title=mname,minReleased=min_released, maxReleased=max_released))
        too = len(search_movie)
        return render_template('user/movies.html', utga=search_movie, too=too)
@app.route('/movie/<int:id>')
def movie(id):
    conn = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
    cur = conn.session()
    movie = list(cur.run("match(m:Movie) where id(m) = $id return m.title as title, m.image as image, m.released as released, m.tagline as tagline", id=id))
    actors = list(cur.run("""
        match(m:Movie)<-[r:ACTED_IN]-(p:Person)
        where id(m) = $id
        return id(p) as actorID, p.name as name, r.roles as roles
        """, id=id))
    directors = list(cur.run("""
        match(m:Movie)<-[:DIRECTED]-(d:Person)
        where id(m) = $id
        return id(d) as directorID, d.name as name
        """, id=id))
    writers = list(cur.run("""
        match(m:Movie)<-[:WROTE]-(d:Person)
        where id(m) = $id
        return d.name as name
        """,id=id))
    producers = list(cur.run("""
        match(m:Movie)<-[:PRODUCED]-(p:Person)
        where id(m) = $id
        return p.name as name
        """,id=id))

    comments = list(cur.run("""
        match(m:Movie)<-[r:REVIEWED]-(p:Person)
        where id(m) = $id
        return p.name as name, r.summary as summary, r.rating as rating
        """, id=id))
    context = {
        "movie" : movie[0],
        "actors": actors,
        "directors": directors,
        "writers": writers,
        "producers": producers,
        "comments": comments
    }
    
    return render_template('user/movie_detail.html', data = context)
    




@app.route("/Жүжигчин", methods = ['GET', 'POST'])
def actors(limit=9):
    if request.method == 'GET':
        page = int(request.args.get("page",1))
        start = (page-1) * limit
        con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = con.session()
        actors = cur.run("match (p:Person)-[:ACTED_IN]->(m:Movie) return distinct p.name as name, p.born as born, p.image as image")
        latest = list(actors)
        too = len(latest)
        paginate = Pagination(page=page, per_page=limit, total=too)
        paged_actors = cur.run("match (p:Person)-[:ACTED_IN]->(m:Movie) return distinct p.name as name, p.born as born, p.image as image, id(p) as actorID SKIP $skip LIMIT $limit", skip=start, limit=limit)
        return render_template('user/actors.html', utga=paged_actors, too=too, paginate=paginate)
    elif request.method == 'POST':
        title = request.form['txtMovieTitle']
        print(title)
        min_released = request.form.get('minReleased')
        max_released = request.form.get('maxReleased')
        con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = con.session()
        search_movie = list(cur.run('''
        MATCH (m:Movie)
    WHERE toLower(m.title) CONTAINS toLower($title)
    AND ($minReleased IS NULL AND $maxReleased IS NULL OR (m.released >= $minReleased AND m.released <= $maxReleased))
    RETURN m.title AS title, m.released AS released, m.image AS image, id(m) AS movieID
''', title=title,minReleased=min_released, maxReleased=max_released))
        too = len(search_movie)
        return render_template('user/actors.html', utga=search_movie, too=too)
@app.route('/Жүжигчин/<int:id>')
def actor(id):
    conn = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
    cur = conn.session()
    actor_detail = list(cur.run("""
        match(p:Person) where id(p) = $id
        return p.name as name, p.image as image, p.born as born
        """, id=id))
    acted_movies = list(cur.run(""" match(m:Movie)<-[:ACTED_IN]-(p:Person) 
        where id(p) = $id return m.title as title, m.released as released, id(m) as movieID
    """, id=id))

    context = {
        "actor": actor_detail[0],
        "movies": acted_movies
    }
    return render_template("user/actor.html", context=context)  


@app.route("/Найруулагч", methods = ['GET', 'POST'])
def directors(limit=9):
    if request.method == 'GET':
        page = int(request.args.get("page",1))
        start = (page-1) * limit
        con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = con.session()
        actors = cur.run("match (p:Person)-[:DIRECTED]->(m:Movie) return distinct p.name as name, p.born as born, p.image as image")
        latest = list(actors)
        too = len(latest)
        paginate = Pagination(page=page, per_page=limit, total=too)
        paged_actors = cur.run("match (p:Person)-[:DIRECTED]->(m:Movie) return distinct p.name as name, p.born as born, p.image as image, id(p) as directorID SKIP $skip LIMIT $limit", skip=start, limit=limit)
        return render_template('user/directors.html', utga=paged_actors, too=too, paginate=paginate)
    elif request.method == 'POST':
        title = request.form['txtMovieTitle']
        print(title)
        min_released = request.form.get('minReleased')
        max_released = request.form.get('maxReleased')
        con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = con.session()
        search_movie = list(cur.run('''
        MATCH (m:Movie)
    WHERE toLower(m.title) CONTAINS toLower($title)
    RETURN m.title AS title, m.released AS released, m.image AS image, id(m) AS directorID
''', title=title,minReleased=min_released, maxReleased=max_released))
        too = len(search_movie)
        return render_template('user/directors.html', utga=search_movie, too=too)
@app.route('/Найруулагч/<int:id>')
def director(id):
    conn = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
    cur = conn.session()
    actor_detail = list(cur.run("""
        match(p:Person) where id(p) = $id
        return p.name as name, p.image as image, p.born as born
        """, id=id))
    acted_movies = list(cur.run(""" match(m:Movie)<-[:DIRECTED]-(p:Person) 
        where id(p) = $id return m.title as title, m.released as released, id(m) as movieID
    """, id=id))

    context = {
        "actor": actor_detail[0],
        "movies": acted_movies
    }
    return render_template("user/director.html", context=context)  





@app.route("/Продюсер", methods = ['GET', 'POST'])
def producers(limit=9):
    if request.method == 'GET':
        page = int(request.args.get("page",1))
        start = (page-1) * limit
        con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = con.session()
        actors = cur.run("match (p:Person)-[:PRODUCED]->(m:Movie) return distinct p.name as name, p.born as born, p.image as image")
        latest = list(actors)
        too = len(latest)
        paginate = Pagination(page=page, per_page=limit, total=too)
        paged_actors = cur.run("match (p:Person)-[:PRODUCED]->(m:Movie) return distinct p.name as name, p.born as born, p.image as image, id(p) as producerID SKIP $skip LIMIT $limit", skip=start, limit=limit)
        return render_template('user/producers.html', utga=paged_actors, too=too, paginate=paginate)
    elif request.method == 'POST':
        title = request.form['txtMovieTitle']
        print(title)
        min_released = request.form.get('minReleased')
        max_released = request.form.get('maxReleased')
        con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = con.session()
        search_movie = list(cur.run('''
        MATCH (m:Movie)
    WHERE toLower(m.title) CONTAINS toLower($title)
    RETURN m.title AS title, m.released AS released, m.image AS image, id(m) AS movieID
''', title=title,minReleased=min_released, maxReleased=max_released))
        too = len(search_movie)
        return render_template('user/producers.html', utga=search_movie, too=too)
@app.route('/Продюсер/<int:id>')
def producer(id):
    conn = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
    cur = conn.session()
    actor_detail = list(cur.run("""
        match(p:Person) where id(p) = $id
        return p.name as name, p.image as image, p.born as born
        """, id=id))
    acted_movies = list(cur.run(""" match(m:Movie)<-[:PRODUCED]-(p:Person) 
        where id(p) = $id return m.title as title, m.released as released, id(m) as movieID
    """, id=id))

    context = {
        "producer": actor_detail[0],
        "movies": acted_movies
    }
    return render_template("user/producer.html", context=context)  






@app.route("/Зохиолч", methods = ['GET', 'POST'])
def wrotes(limit=9):
    if request.method == 'GET':
        page = int(request.args.get("page",1))
        start = (page-1) * limit
        con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = con.session()
        actors = cur.run("match (p:Person)-[:WROTE]->(m:Movie) return distinct p.name as name, p.born as born, p.image as image")
        latest = list(actors)
        too = len(latest)
        paginate = Pagination(page=page, per_page=limit, total=too)
        paged_actors = cur.run("match (p:Person)-[:WROTE]->(m:Movie) return distinct p.name as name, p.born as born, p.image as image, id(p) as wroteID SKIP $skip LIMIT $limit", skip=start, limit=limit)
        return render_template('user/wrotes.html', utga=paged_actors, too=too, paginate=paginate)
    elif request.method == 'POST':
        title = request.form['txtMovieTitle']
        print(title)
        min_released = request.form.get('minReleased')
        max_released = request.form.get('maxReleased')
        con = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = con.session()
        search_movie = list(cur.run('''
        MATCH (m:Movie)
    WHERE toLower(m.title) CONTAINS toLower($title)
    RETURN m.title AS title, m.released AS released, m.image AS image, id(m) AS movieID
''', title=title,minReleased=min_released, maxReleased=max_released))
        too = len(search_movie)
        return render_template('user/wrotes.html', utga=search_movie, too=too)
@app.route('/Зохиолч/<int:id>')
def wrote(id):
    conn = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
    cur = conn.session()
    actor_detail = list(cur.run("""
        match(p:Person) where id(p) = $id
        return p.name as name, p.image as image, p.born as born
        """, id=id))
    acted_movies = list(cur.run(""" match(m:Movie)<-[:WROTE]-(p:Person) 
        where id(p) = $id return m.title as title, m.released as released, id(m) as movieID
    """, id=id))

    context = {
        "wrote": actor_detail[0],
        "movies": acted_movies
    }
    return render_template("user/wrote.html", context=context)  
### user end ###

### admin start ###

# admin nuur huudas
@app.route('/admin')
def admin_index():
    return render_template('admin/admin.html')

# admin kino nemeh heseg
@app.route('/admin/movie/create',  methods = ['GET', 'POST'])
def movie_create():
    resp = "Create Movie"
    if request.method == 'POST':
        title = request.form["title"]
        tagline = request.form["tagline"]
        released = request.form["released"]
        image = request.files['img']
        image.save("./static/movies/" + title + ".jpg")
        conn = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = conn.session()
        movie = list(cur.run("""merge (m:Movie 
                        {title:$title,released:$released,tagline:$tagline,image: "/static/movies/"+$title + ".jpg"})
                        on match set m.isCreated=false
                        on create set m.isCreated=true
                        return m.isCreated as result""", title=title, released=released, tagline=tagline))
        if(movie[0]["result"]):
            resp = "Amjilttai"
        else:
            resp = "Amjiltgui aldaa"
            
    return render_template('admin/movie_create.html', resp = resp)

@app.route('/admin/person/create',  methods = ['GET', 'POST'])
def person_create():
    resp = "Create Person"
    if request.method == 'POST':
        name = request.form["name"]
        born = request.form["born"]
        image = request.files['img']
        image.save("./static/media/" + name + ".jpg")
        conn = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = conn.session()
        person = list(cur.run("""merge (m:Person 
                        {name:$name,born:$born,image: "/static/media/"+$name + ".jpg"})
                        on match set m.isCreated=false
                        on create set m.isCreated=true
                        return m.isCreated as result""", name=name, born=born))
        if(person[0]["result"]):
            resp = "Amjilttai"
        else:
            resp = "Amjiltgui aldaa"
            
    return render_template('admin/person_create.html', resp = resp)
@app.route('/admin/moviegroup/create',  methods = ['GET', 'POST'])
def moviegroup_create():
    resp = "Create Movie Group"
    if request.method == 'GET':
        
        conn = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = conn.session()
        movies = list(cur.run("""
                        MATCH(m:Movie) 
                        return m.title as title
                        """))
        persons = list(cur.run("""
                        match (m:Person) 
                        return m.name as name
                        """))
        rel = list(cur.run("""
                        match (m:Movie)<-[r]-(p:Person)
                        return distinct type(r) as relationship
                        """))
        context = {
        "rel" : rel,
        "persons": persons,
        "movies": movies,
    }   
        return render_template('admin/moviegroup_create.html', data=context )

    else:
        name = request.form["name"]
        relationship = request.form["relationship"]
        title = request.form['title']
        roles = request.form.get('roles')
        conn = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "12345678"))
        cur = conn.session()
        if roles is None:
            query = f"""
        MATCH (p:Person {{name: $name}})
        MATCH (m:Movie {{title: $title}})
        MERGE (p)-[r:{relationship}]->(m)
        RETURN r
    """
        else:
            query = """
        MATCH (p:Person {name: $name})
        MATCH (m:Movie {title: $title})
        MERGE (p)-[r:ACTED_IN {roles: [$roles]}]->(m)
        RETURN r
    """

        group = list(cur.run(query, name=name, title=title, roles=roles))
        print(group[0])
        if(group[0]):
            resp = "Amjilttai"
        else:
            resp = "Amjiltgui aldaa"

        return render_template('admin/moviegroup_create.html', resp=resp )    
        
        
            
    


### admin end ###

if __name__=='__main__':
    app.run(port="5001",debug=True)