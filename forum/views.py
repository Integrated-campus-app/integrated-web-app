from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Question

@login_required
def question_list(request):
    questions = Question.objects.filter(is_deleted=False)
    return render(request, 'forum/question_list.html', {'questions': questions})

@login_required
def ask_question(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body')
        Question.objects.create(user=request.user, title=title, body=body)
        return redirect('question_list')
    return render(request, 'forum/ask_question.html')

def question_detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'forum/question_detail.html', {'question': question})