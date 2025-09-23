from flask import Blueprint, render_template, request, redirect, url_for
from .models import db, Group, Family, Member, TaxRecord
from datetime import datetime
from sqlalchemy import func

main = Blueprint('main', __name__)

@main.route('/')
def index():
    families = Family.query.all()
    return render_template('index.html', families=families)

@main.route('/add_family', methods=['GET', 'POST'])
def add_family():
    if request.method == 'POST':
        group_id = request.form.get('group_id')
        name = request.form.get('name')
        family = Family(name=name, group_id=group_id)
        db.session.add(family)
        db.session.commit()
        return redirect(url_for('main.index'))
    groups = Group.query.all()
    return render_template('add_family.html', groups=groups)

@main.route('/add_member/<int:family_id>', methods=['GET', 'POST'])
def add_member(family_id):
    if request.method == 'POST':
        name = request.form['name']
        dob = datetime.strptime(request.form['dob'], '%Y-%m-%d')
        gender = request.form['gender']
        mobile = request.form['mobile']
        wedding_date = datetime.strptime(request.form['wedding_date'], '%Y-%m-%d') if request.form['wedding_date'] else None
        is_deceased = 'is_deceased' in request.form
        relation = request.form['relation']
        new_member = Member(
            family_id=family_id,
            name=name,
            dob=dob,
            gender=gender,
            mobile=mobile,
            wedding_date=wedding_date,
            is_deceased=is_deceased,
            relation=relation
        )
        db.session.add(new_member)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('add_member.html', family_id=family_id)

@main.route('/add_tax/<int:member_id>', methods=['GET', 'POST'])
def add_tax(member_id):
    member = Member.query.get(member_id)
    if request.method == 'POST':
        year = int(request.form['year'])
        term = int(request.form['term'])
        amount = float(request.form['amount'])
        paid_on = datetime.strptime(request.form['paid_on'], '%Y-%m-%d')
        tax = TaxRecord(member_id=member_id, year=year, term=term, amount=amount, paid_on=paid_on)
        db.session.add(tax)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('add_tax.html', member=member, now=datetime.today())

@main.route('/eligible_members')
def eligible_members():
    today = datetime.today()
    eligible = Member.query.filter(
        Member.gender == 'Male',
        Member.is_deceased == False,
        Member.dob <= datetime(today.year - 18, today.month, today.day)
    ).all()
    return render_template('eligible_members.html', members=eligible)

@main.route('/dashboard_default')
def dashboard_default():
    records = TaxRecord.query.all()
    summary = {}
    for r in records:
        key = f"{r.year}-T{r.term}"
        summary.setdefault(key, 0)
        summary[key] += r.amount
    return render_template('dashboard.html', summary=summary)

@main.route('/group_summary')
def group_summary():
    from sqlalchemy import func
    results = db.session.query(
        Family.group_id,
        func.sum(TaxRecord.amount)
    ).join(Member).join(Family).group_by(Family.group_id).all()

    summary = []
    for group_id, total in results:
        group = Group.query.get(group_id)
        summary.append({
            'group_name': group.name,
            'total': total
        })

    return render_template('group_summary.html', summary=summary)

@main.route('/export_excel_default')
def export_excel_default():
    import pandas as pd
    from flask import Response

    records = db.session.query(
        Member.name,
        TaxRecord.year,
        TaxRecord.term,
        TaxRecord.amount,
        TaxRecord.paid_on
    ).join(TaxRecord).all()

    df = pd.DataFrame(records, columns=['Name', 'Year', 'Term', 'Amount', 'Paid On'])
    output = df.to_excel(index=False, engine='openpyxl')

    response = Response(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response.headers['Content-Disposition'] = 'attachment; filename=tax_report.xlsx'
    return response

@main.route('/export_pdf_default')
def export_pdf_default():
    from weasyprint import HTML
    from flask import make_response

    html = render_template('dashboard.html')  # reuse your dashboard
    pdf = HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=tax_report.pdf'
    return response

@main.route('/export_excel')
def export_excel():
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    from sqlalchemy import func

    results = db.session.query(
        Group.name.label('Group'),
        func.sum(TaxRecord.amount).label('Total Tax')
    ).join(Family, Family.group_id == Group.id)\
     .join(Member, Member.family_id == Family.id)\
     .join(TaxRecord, TaxRecord.member_id == Member.id)\
     .group_by(Group.name).all()

    df = pd.DataFrame(results, columns=['Group', 'Total Tax'])
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return send_file(output, download_name="group_tax_summary.xlsx", as_attachment=True)

@main.route('/export_pdf')
def export_pdf():
    from weasyprint import HTML, CSS
    from flask import make_response
    import os

    html = render_template('dashboard.html')
    css = CSS(string='''
        @page { size: A4; margin: 1cm }
        body { font-family: sans-serif; }
        h2 { color: #2c3e50; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    ''')

    logo_path = os.path.join('app', 'static', 'logo.png')  # Add your logo here
    html_with_logo = f'''
    <html>
    <body>
        <img src="{logo_path}" width="100"><br>
        {html}
    </body>
    </html>
    '''

    pdf = HTML(string=html_with_logo).write_pdf(stylesheets=[css])
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=tax_report.pdf'
    return response

@main.route('/export_filtered_excel', methods=['POST'])
def export_filtered_excel():
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    from sqlalchemy import and_

    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    term = request.form.get('term')

    query = db.session.query(
        Member.name.label('Name'),
        TaxRecord.year.label('Year'),
        TaxRecord.term.label('Term'),
        TaxRecord.amount.label('Amount'),
        TaxRecord.paid_on.label('Paid On')
    ).join(TaxRecord)

    filters = []
    if start_date:
        filters.append(TaxRecord.paid_on >= start_date)
    if end_date:
        filters.append(TaxRecord.paid_on <= end_date)
    if term:
        filters.append(TaxRecord.term == int(term))

    if filters:
        query = query.filter(and_(*filters))

    results = query.all()
    df = pd.DataFrame(results, columns=['Name', 'Year', 'Term', 'Amount', 'Paid On'])

    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return send_file(output, download_name="filtered_tax_report.xlsx", as_attachment=True)

@main.route('/export_filtered_pdf', methods=['POST'])
def export_filtered_pdf():
    from weasyprint import HTML, CSS
    from flask import make_response
    from sqlalchemy import and_

    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    term = request.form.get('term')

    query = db.session.query(
        Member.name,
        TaxRecord.year,
        TaxRecord.term,
        TaxRecord.amount,
        TaxRecord.paid_on
    ).join(TaxRecord)

    filters = []
    if start_date:
        filters.append(TaxRecord.paid_on >= start_date)
    if end_date:
        filters.append(TaxRecord.paid_on <= end_date)
    if term:
        filters.append(TaxRecord.term == int(term))

    if filters:
        query = query.filter(and_(*filters))

    records = query.all()

    html_content = render_template('filtered_pdf.html', records=records)
    css = CSS(string='''
        body { font-family: sans-serif; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background-color: #f2f2f2; }
    ''')

    pdf = HTML(string=html_content).write_pdf(stylesheets=[css])
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=filtered_tax_report.pdf'
    return response

@main.route('/export_group_excel', methods=['POST'])
def export_group_excel():
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    from sqlalchemy import and_, func

    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    term = request.form.get('term')

    query = db.session.query(
        Group.name.label('Group'),
        func.sum(TaxRecord.amount).label('Total Tax')
    ).join(Family, Family.group_id == Group.id)\
     .join(Member, Member.family_id == Family.id)\
     .join(TaxRecord, TaxRecord.member_id == Member.id)

    filters = []
    if start_date:
        filters.append(TaxRecord.paid_on >= start_date)
    if end_date:
        filters.append(TaxRecord.paid_on <= end_date)
    if term:
        filters.append(TaxRecord.term == int(term))

    if filters:
        query = query.filter(and_(*filters))

    query = query.group_by(Group.name)
    results = query.all()

    df = pd.DataFrame(results, columns=['Group', 'Total Tax'])
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return send_file(output, download_name="group_filtered_tax.xlsx", as_attachment=True)

@main.route('/group_leader_export/<int:leader_id>')
def group_leader_export(leader_id):
    group = Group.query.filter_by(group_leader_id=leader_id).first()
    members = Member.query.join(Family).filter(Family.group_id == group.id).all()
    # Export logic here

from flask_login import current_user

@main.route('/send_message', methods=['POST'])
def send_message():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    # Send WhatsApp or SMS
    
@main.route('/view_family/<int:family_id>')
def view_family(family_id):
    family = Family.query.get(family_id)
    members = Member.query.filter_by(family_id=family_id).all()
    return render_template('view_family.html', family=family, members=members)

@main.route('/index_summary')
def index_summary():
    families = Family.query.all()
    members = Member.query.all()
    total_tax = db.session.query(func.sum(TaxRecord.amount)).scalar() or 0

    return render_template(
        'index.html',
        families=families,
        total_members=len(members),
        total_tax=total_tax
    )

@main.route('/search')
def search():
    return render_template('search.html')
#JENKINS WORKED FINE HERE
#HOPE JENKINS WORKS THIS TIME6 --- IGNORE ---