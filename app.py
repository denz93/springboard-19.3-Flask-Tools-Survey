from flask import Flask, render_template, session, redirect, request
from surveys import surveys, Question, Survey
import json 

app = Flask(__name__)
app.secret_key = '6kF5#%+S!FMpeRw_jD8LYWQfgj9Te&'

surveyMaxId = 2

def first_missing_id(id_set, length):
  for i in range(length):
    if str(i) not in id_set:
      return i 
  return -1

def dict2question(d):
  if not isinstance(d, dict):
    return None 
  question = Question(d['question'], d['choices'], d['allow_text'])
  return question

def dict2survey(d):
  if not isinstance(d, dict):
    return None
  questions = []
  for question_dict in d['questions']:
    question = dict2question(question_dict)
    questions.append(question)

  survey = Survey(d['title'], d['instructions'], questions)
  return survey

@app.route('/')
def home_page():
  answers_map = {}
  for survey_id in surveys:
    answers_map[survey_id] = session[survey_id] if survey_id in session else {}
  return render_template('home.html', surveys=surveys, answers_map = answers_map)

@app.route('/surveys/<string:survey_id>', methods=['POST'])
def answer_survey(survey_id):
  if survey_id not in session:
    session[survey_id] = {}

  answers = session[survey_id]
  survey = surveys[survey_id]

  if len(answers) < len(survey.questions):
    question_id = first_missing_id(answers.keys(), len(survey.questions))
    return redirect(f'/surveys/{survey_id}/questions/{question_id}', code=303)
  else:
    return redirect(f'/thankyou/{survey_id}', code=303)
  
@app.route('/surveys/<survey_id>/questions/<int:question_id>')
def show_question(survey_id, question_id):
  if survey_id not in session:
    return redirect('/', code=303)
  
  answers = session[survey_id]
  survey = surveys[survey_id]
  
  is_invalid_question_id = question_id >= len(survey.questions) or \
    question_id < 0
  
  if is_invalid_question_id:
    return redirect(f'/surveys/{survey_id}/questions/0', code=303)
  

  return render_template('question.html', 
                         survey=survey,
                         survey_id=survey_id,
                         answers=answers,
                         question_id=question_id,
                         question=survey.questions[question_id])

@app.route('/surveys/<survey_id>/questions/<int:question_id>', methods=['POST'])
def answer_question(survey_id, question_id):
  if survey_id not in session:
    return redirect('/', code=303)
  
  survey = surveys[survey_id]

  if question_id >= len(survey.questions) or question_id < 0:
    return redirect(f'/surveys/{survey_id}/questions/0', code=303)
  if 'answer' not in request.form:
    return redirect(f'/surveys/{survey_id}/questions/{question_id}', code=303)
  
  question = survey.questions[question_id]
  answers = session[survey_id]
  answer = request.form['answer']
  comment = request.form['comment'] if 'comment' in request.form and question.allow_text else None

  answers[str(question_id)] = {
    'answer': answer,
    'comment': comment
  }

  session[survey_id] = answers
  
  if len(answers) == len(survey.questions):
    return redirect(f'/thankyou/{survey_id}', code=303)
  
  if question_id + 1 < len(survey.questions):
    return redirect(f'/surveys/{survey_id}/questions/{question_id+1}', code=303)
  
  next_id = first_missing_id(answers.keys(), len(survey.questions))
  return redirect(f'/surveys/{survey_id}/questions/{next_id}', code=303) 
  
@app.route('/thankyou/<survey_id>')
def thankyou_page(survey_id):
  if survey_id not in session:
    redirect('/', code=303)
  
  answers = session[survey_id]
  survey = surveys[survey_id]

  if len(answers) < len(survey.questions):
    next_id = first_missing_id(answers.keys(), len(survey.questions))
    return redirect(f'/surveys/{survey_id}/questions/{next_id}', code=303)
  
  return render_template('thankyou.html', answers=answers, survey=survey)

@app.route('/new-survey')
def new_survey_page():
  draft_survey = session.get('draft_survey')

  if 'draft_survey' not in session:
    draft_survey = session.setdefault(
      'draft_survey',
      { 'title': '', 'instructions': '', 'questions': []}
    )
  print(draft_survey)
  return render_template('new-survey.html', draft_survey=draft_survey)

@app.route('/draft/survey', methods=['POST'])
def update_draft_survey():
  draft_survey = session.get('draft_survey')
  if 'draft_survey' not in session:
    draft_survey = session.setdefault(
      'draft_survey',
      { 'title': '', 'instructions': '', 'questions': []}
    )
  print(draft_survey)
  title = request.form.get('title')
  instructions = request.form.get('instructions')
  draft_survey['title'] = title 
  draft_survey['instructions'] = instructions
  session['draft_survey'] = draft_survey 
  session.modified = True
  session.new
  global surveyMaxId
  if 'publish' in request.form and len(draft_survey['questions']) > 0:
    surveys[str(surveyMaxId)] = dict2survey(draft_survey)
    surveyMaxId += 1
    session.pop('draft_survey')
    return redirect('/', code=303)
  return redirect('/new-survey', code=303)
  

@app.route('/draft/question', methods=['POST'])
def insert_question():
  draft_survey = session.get('draft_survey')
  choices = request.form.getlist('choices')
  if len(choices) == 0:
    return redirect('/new-survey', code=303)
  question = {
    'question': request.form.get('question'),
    'choices': choices,
    'allow_text': request.form['allow_text']
  }

  draft_survey['questions'].append(question)
  session['draft_survey'] = draft_survey
  return redirect('/new-survey', code=303)
 
