from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Job, CostItem
from . import db
import re  # Import the regex module
from sqlalchemy.exc import IntegrityError
from math import floor

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/job-dashboard', methods=['GET', 'POST'])
@login_required
def job_dashboard():
    if request.method == 'POST':
        # Get form data
        customer_first_name = request.form.get('customer_first_name')
        customer_last_name = request.form.get('customer_last_name')
        customer_email = request.form.get('customer_email')  # Get the email field
        address_street = request.form.get('address_street')
        address_suburb = request.form.get('address_suburb')
        address_city = request.form.get('address_city')
        address_state = request.form.get('address_state')
        address_postcode = request.form.get('address_postcode')  # Get the postcode
        budget = request.form.get('budget')
        stage = request.form.get('stage')

        # Validate required fields
        if not all([customer_first_name, customer_last_name, address_street, address_suburb, address_city, address_state, address_postcode, budget, stage]):
            flash('All fields are required. Please fill out the form completely.', category='error')
        elif customer_email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', customer_email):
            flash('Invalid email address. Please enter a valid email.', category='error')
        else:
            # Generate unique job number
            last_job = Job.query.order_by(Job.id.desc()).first()
            job_number = f"MVC{(last_job.id + 1) if last_job else 1:03d}"

            # Save the job to the database
            new_job = Job(
                job_number=job_number,
                customer_first_name=customer_first_name,
                customer_last_name=customer_last_name,
                customer_email=customer_email,  # Save the email
                address_street=address_street,
                address_suburb=address_suburb,
                address_city=address_city,
                address_state=address_state,
                address_postcode=address_postcode,  # Save the postcode
                budget=budget,
                status="Pending",  # Default status
                stage=stage,
                user_id=current_user.id
            )
            db.session.add(new_job)
            db.session.commit()

            flash(f"Job {job_number} added successfully!", category='success')

    # Query all jobs
    jobs = Job.query.all()
    return render_template("job_dashboard.html", user=current_user, jobs=jobs)

@views.route('/edit-job', methods=['POST'])
@login_required
def edit_job():
    job_id = request.form.get('job_id')
    job = Job.query.get(job_id)

    if job:
        job.customer_first_name = request.form.get('customer_first_name')
        job.customer_last_name = request.form.get('customer_last_name')
        job.address_street = request.form.get('address_street')
        job.budget = request.form.get('budget')
        job.stage = request.form.get('stage')
        db.session.commit()
        flash('Job updated successfully!', category='success')
    else:
        flash('Job not found.', category='error')

    return redirect(url_for('views.job_dashboard'))


@views.route('/delete-job', methods=['POST'])
@login_required
def delete_job():
    job_id = request.form.get('job_id')  # Retrieve the job_id from the form
    print(f"Received job_id: {job_id}")  # Debugging

    job = Job.query.get(job_id)  # Query the job by its ID

    if job:
        db.session.delete(job)  # Delete the job from the database
        db.session.commit()
        flash('Job deleted successfully!', category='success')
    else:
        flash('Job not found.', category='error')

    return redirect(url_for('views.job_dashboard'))

@views.route('/estimating', methods=['GET'])
@login_required
def estimating():
    return render_template("estimating.html", user=current_user)

@views.route('/job-cost', methods=['GET', 'POST'])
@login_required
def job_cost():
    selected_job = None
    cost_items = []
    total_budget = 0
    total_committed_cost = 0
    total_actual_cost = 0
    total_cost_to_complete = 0
    total_forecast_at_completion = 0
    total_gain_loss = 0

    if request.method == 'POST':
        job_id = request.form.get('job_id')
        if job_id:
            selected_job = Job.query.get(int(job_id))
            if selected_job:
                cost_items = selected_job.cost_items
                print(f"Cost Items for Job {selected_job.job_number}: {cost_items}")  # Debugging

                # Calculate totals
                for item in cost_items:
                    total_budget += item.budget or 0
                    total_committed_cost += item.committed_cost or 0
                    total_actual_cost += item.actual_cost or 0
                    total_cost_to_complete += item.cost_to_complete or 0
                    total_forecast_at_completion += item.forecast_at_completion or 0
                    total_gain_loss += item.gain_loss or 0

    return render_template(
        "job_cost.html",
        user=current_user,
        jobs=Job.query.all(),
        selected_job=selected_job,
        cost_items=cost_items,
        total_budget=total_budget,
        total_committed_cost=total_committed_cost,
        total_actual_cost=total_actual_cost,
        total_cost_to_complete=total_cost_to_complete,
        total_forecast_at_completion=total_forecast_at_completion,
        total_gain_loss=total_gain_loss,
    )

@views.route('/job-cost/estimate/<int:job_id>', methods=['GET', 'POST'])
@login_required
def job_cost_estimate(job_id):
    job = Job.query.get_or_404(job_id)
    cost_items = job.cost_items

    if request.method == 'POST':
        try:
            # Update existing cost items
            for item in cost_items:
                # Retrieve form data for each cost item
                cost_code = request.form.get(f'cost_code_{item.id}')
                description = request.form.get(f'description_{item.id}')
                budget = float(request.form.get(f'budget_{item.id}') or 0)
                committed_cost = float(request.form.get(f'committed_cost_{item.id}') or 0)
                actual_cost = float(request.form.get(f'actual_cost_{item.id}') or 0)

                # Calculate Cost to Complete
                if committed_cost == 0:
                    cost_to_complete = max(0, budget - actual_cost)
                else:
                    cost_to_complete = max(0, committed_cost - actual_cost)

                # Recalculate Forecast at Completion
                forecast_at_completion = cost_to_complete + actual_cost

                # Recalculate Gain/Loss
                gain_loss = budget - forecast_at_completion

                # Update cost item attributes
                item.cost_code = cost_code
                item.description = description
                item.budget = budget
                item.committed_cost = committed_cost
                item.actual_cost = actual_cost
                item.cost_to_complete = cost_to_complete
                item.forecast_at_completion = forecast_at_completion
                item.gain_loss = gain_loss

            # Create new cost items
            new_cost_item_count = int(request.form.get('new_cost_item_count', 0))
            for i in range(new_cost_item_count):
                cost_code = request.form.get(f'new_cost_code_{i}')
                description = request.form.get(f'new_description_{i}')
                budget = float(request.form.get(f'new_budget_{i}') or 0)
                committed_cost = float(request.form.get(f'new_committed_cost_{i}') or 0)
                actual_cost = float(request.form.get(f'new_actual_cost_{i}') or 0)

                 # Calculate Cost to Complete
                if committed_cost == 0:
                    cost_to_complete = max(0, budget - actual_cost)
                else:
                    cost_to_complete = max(0, committed_cost - actual_cost)

                # Recalculate Forecast at Completion
                forecast_at_completion = cost_to_complete + actual_cost

                # Recalculate Gain/Loss
                gain_loss = budget - forecast_at_completion

                if cost_code and description:
                    new_item = CostItem(
                        cost_code=cost_code,
                        description=description,
                        budget=budget,
                        committed_cost=committed_cost,
                        actual_cost=actual_cost,
                        cost_to_complete=cost_to_complete,
                        forecast_at_completion=forecast_at_completion,
                        gain_loss=gain_loss,
                        job_id=job.id
                    )
                    db.session.add(new_item)

            db.session.commit()
            flash('Estimates saved successfully!', category='success')
            return redirect(url_for('views.job_cost'))

        except ValueError:
            db.session.rollback()
            flash('Invalid input. Please enter valid numbers.', category='error')
        except IntegrityError as e:
            db.session.rollback()
            flash(f'Database error: {e}', category='error')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', category='error')

    return render_template("job_cost_estimate.html", user=current_user, job=job, cost_items=cost_items)


@views.route('/estimate-entry-sheet/<int:job_id>', methods=['GET', 'POST'])
@login_required
def estimate_entry_sheet(job_id):
    job = Job.query.get_or_404(job_id)
    cost_items = job.cost_items

    if request.method == 'POST':
        try:
            # Update existing cost items
            for item in cost_items:
                # Retrieve form data for each cost item
                cost_code = request.form.get(f'cost_code_{item.id}')
                description = request.form.get(f'description_{item.id}')
                qty = float(request.form.get(f'qty_{item.id}') or 0)
                unit = request.form.get(f'unit_{item.id}')
                value = float(request.form.get(f'value_{item.id}') or 0)
                budget = qty * value

                # Update cost item attributes
                item.cost_code = cost_code
                item.description = description
                item.qty = qty
                item.unit = unit
                item.value = value
                item.budget = budget

            # Create new cost items
            new_cost_item_count = int(request.form.get('new_cost_item_count', 0))
            for i in range(new_cost_item_count):
                cost_code = request.form.get(f'new_cost_code_{i}')
                description = request.form.get(f'new_description_{i}')
                qty = float(request.form.get(f'new_qty_{i}') or 0)
                unit = request.form.get(f'new_unit_{i}')
                value = float(request.form.get(f'new_value_{i}') or 0)
                budget = qty * value

                if cost_code and description:
                    new_item = CostItem(
                        cost_code=cost_code,
                        description=description,
                        qty=qty,
                        unit=unit,
                        value=value,
                        budget=budget,
                        job_id=job.id
                    )
                    db.session.add(new_item)

            db.session.commit()
            flash('Estimates saved successfully!', category='success')
            return redirect(url_for('views.job_cost'))

        except ValueError:
            db.session.rollback()
            flash('Invalid input. Please enter valid numbers.', category='error')
        except IntegrityError as e:
            db.session.rollback()
            flash(f'Database error: {e}', category='error')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', category='error')

    return render_template("estimate_entry_sheet.html", user=current_user, job=job, cost_items=cost_items)


@views.route('/cost-to-complete/<int:job_id>', methods=['GET', 'POST'])
@login_required
def cost_to_complete(job_id):
    job = Job.query.get_or_404(job_id)
    cost_items = job.cost_items

    if request.method == 'POST':
        try:
            # Update cost to complete for each item
            for item in cost_items:
                cost_to_complete = float(request.form.get(f'cost_to_complete_{item.id}') or 0)
                item.cost_to_complete = cost_to_complete

                # Recalculate Forecast at Completion
                forecast_at_completion = cost_to_complete + item.actual_cost

                # Recalculate Gain/Loss
                gain_loss = item.budget - forecast_at_completion

                # Update cost item attributes
                item.forecast_at_completion = forecast_at_completion
                item.gain_loss = gain_loss

            db.session.commit()
            flash('Cost to Complete updated successfully!', category='success')
            return redirect(url_for('views.job_cost'))

        except ValueError:
            db.session.rollback()
            flash('Invalid input. Please enter valid numbers.', category='error')
        except IntegrityError as e:
            db.session.rollback()
            flash(f'Database error: {e}', category='error')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', category='error')

    return render_template("cost_to_complete.html", user=current_user, job=job, cost_items=cost_items)


@views.route('/purchasing', methods=['GET'])
@login_required
def purchasing():
    return render_template("purchasing.html", user=current_user)

@views.route('/progress-claims', methods=['GET'])
@login_required
def progress_claims():
    return render_template("progress_claims.html", user=current_user)

@views.route('/variations', methods=['GET'])
@login_required
def variations():
    return render_template("variations.html", user=current_user)

@views.route('/program', methods=['GET'])
@login_required
def program():
    return render_template("program.html", user=current_user)

@views.route('/contract-admin', methods=['GET'])
@login_required
def contract_admin():
    return render_template("contract_admin.html", user=current_user)