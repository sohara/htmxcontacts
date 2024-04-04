from flask import Flask, redirect, request, render_template, flash, send_file
from contacts_model import Contact, Archiver

Contact.load_db()

app = Flask(__name__)
app.secret_key = b"hypermedia rocks"


@app.route("/")
def index():
    return redirect("/contacts")


@app.route("/contacts")
def contacts():
    search = request.args.get("q")
    page = int(request.args.get("page", 1))
    if search is not None:
        contacts_set = Contact.search(search)
        if request.headers.get("HX-Trigger") == "search":
            return render_template("rows.html", contacts=contacts_set)
    else:
        contacts_set = Contact.all(page)

    return render_template(
        "index.html", contacts=contacts_set, page=page, archiver=Archiver.get()
    )


@app.route("/contacts/archive", methods=["POST"])
def start_archive():
    archiver = Archiver.get()
    archiver.run()
    return render_template("archive-ui.html", archiver=archiver)


@app.route("/contacts/archive", methods=["GET"])
def archive_status():
    archiver = Archiver.get()
    archiver.run()
    return render_template("archive-ui.html", archiver=archiver)


@app.route("/contacts/archive", methods=["DELETE"])
def reset_archive():
    archiver = Archiver.get()
    archiver.reset()
    return render_template("archive-ui.html", archiver=archiver)


@app.route("/contacts/archive/file", methods=["GET"])
def archive_content():
    manager = Archiver.get()
    return send_file(manager.archive_file(), "archive.json", as_attachment=True)


@app.route("/contacts/count")
def contacts_count():
    count = Contact.count()
    return "(" + str(count) + " total contacts)"


@app.route("/contacts/new", methods=["GET"])
def contacts_new_get():
    return render_template("new.html", contact=Contact())


@app.route("/contacts/new", methods=["POST"])
def contacts_new():
    c = Contact(
        None,
        request.form["first_name"],
        request.form["last_name"],
        request.form["phone"],
        request.form["email"],
    )
    if c.save():
        flash("Created New Contact!")
        return redirect("/contacts")
    else:
        return render_template("new.html", contact=c)


@app.route("/contacts/<contact_id>")
def contacts_view(contact_id=0):
    contact = Contact.find(contact_id)
    return render_template("show.html", contact=contact)


@app.route("/contacts/<contact_id>/edit", methods=["GET"])
def contacts_edit_get(contact_id=0):
    contact = Contact.find(contact_id)
    return render_template("edit.html", contact=contact)


@app.route("/contacts/<contact_id>/edit", methods=["POST"])
def contacts_edit_post(contact_id=0):
    c = Contact.find(contact_id)
    if c is not None:
        c.update(
            request.form["first_name"],
            request.form["last_name"],
            request.form["phone"],
            request.form["email"],
        )
        if c.save():
            flash("Updated Contact!")
            return redirect("/contacts/" + str(contact_id))
    return render_template("edit.html", contact=c)


@app.route("/contacts", methods=["DELETE"])
def contacts_delete_all():
    contact_ids = list(map(int, request.form.getlist("selected_contact_ids")))
    for contact_id in contact_ids:
        contact = Contact.find(contact_id)
        if contact is not None:
            contact.delete()
    flash("Deleted Contacts!")
    contacts_set = Contact.all()
    return render_template("index.html", contacts=contacts_set, page=1)


@app.route("/contacts/<contact_id>", methods=["DELETE"])
def contacts_delete(contact_id=0):
    contact = Contact.find(contact_id)
    if contact is not None:
        contact.delete()
        if request.headers.get("HX-Trigger") == "delete-btn":
            flash("Deleted Contact!")
            return redirect("/contacts", 303)
        else:
            return ""
    return redirect("/contacts", 303)


@app.route("/contacts/<contact_id>/email", methods=["GET"])
def contacts_email_get(contact_id=0):
    c = Contact.find(contact_id)
    if c is not None:
        c.email = request.args.get("email")
        c.validate()
        return c.errors.get("email") or ""
    return ""
