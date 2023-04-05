from crowdom import base, client, instruction, objects, project, task_spec as spec

from . import lib

classification_function = base.ClassificationFunction(inputs=(objects.Image,), cls=lib.ImageClass)
classification_instruction = base.LocalizedString(
    {'EN': 'Identify the animal in the photo', 'RU': 'Определите, какое животное на фотографии'}
)

classification_task_spec = base.TaskSpec(
    id='dogs-and-cats',
    function=classification_function,
    name=base.LocalizedString({'EN': 'Cat or dog', 'RU': 'Кошка или собака'}),
    description=base.LocalizedString(
        {'EN': 'Identification of animals in photos', 'RU': 'Определение животных на изображениях'}
    ),
    instruction=classification_instruction,
)

classification_task_spec_p_ru = spec.PreparedTaskSpec(classification_task_spec, 'RU')
classification_task_spec_p_en = spec.PreparedTaskSpec(classification_task_spec, 'EN')
classification_task_expert_task_spec_p_ru = spec.PreparedTaskSpec(
    classification_task_spec, 'RU', scenario=project.Scenario.EXPERT_LABELING_OF_TASKS
)
classification_task_expert_task_spec_p_en = spec.PreparedTaskSpec(
    classification_task_spec, 'EN', scenario=project.Scenario.EXPERT_LABELING_OF_TASKS
)
classification_solution_expert_task_spec_p_ru = spec.PreparedTaskSpec(
    classification_task_spec, 'RU', scenario=project.Scenario.EXPERT_LABELING_OF_SOLVED_TASKS
)
classification_solution_expert_task_spec_p_en = spec.PreparedTaskSpec(
    classification_task_spec, 'EN', scenario=project.Scenario.EXPERT_LABELING_OF_SOLVED_TASKS
)

annotation_function = base.AnnotationFunction(inputs=(objects.Audio,), outputs=(objects.Text,))

annotation_instruction = base.LocalizedString({'RU': 'Запишите звучащие на аудио слова', 'EN': 'Transcribe the audio'})

annotation_task_spec = base.TaskSpec(
    id='audio-transcription',
    function=annotation_function,
    name=base.LocalizedString({'EN': 'Audio transcription', 'RU': 'Расшифровка аудио'}),
    description=base.LocalizedString({'EN': 'Transcribe short audios', 'RU': 'Расшифровка коротких аудио'}),
    instruction=annotation_instruction,
)

annotation_task_spec_p_ru = spec.AnnotationTaskSpec(annotation_task_spec, 'RU')
annotation_task_spec_p_en = spec.AnnotationTaskSpec(annotation_task_spec, 'EN')
annotation_task_expert_task_spec_p_ru = spec.AnnotationTaskSpec(
    annotation_task_spec, 'RU', scenario=project.Scenario.EXPERT_LABELING_OF_TASKS
)
annotation_task_expert_task_spec_p_en = spec.AnnotationTaskSpec(
    annotation_task_spec, 'EN', scenario=project.Scenario.EXPERT_LABELING_OF_TASKS
)
annotation_solution_expert_task_spec_p_ru = spec.AnnotationTaskSpec(
    annotation_task_spec, 'RU', scenario=project.Scenario.EXPERT_LABELING_OF_SOLVED_TASKS
)
annotation_solution_expert_task_spec_p_en = spec.AnnotationTaskSpec(
    annotation_task_spec, 'EN', scenario=project.Scenario.EXPERT_LABELING_OF_SOLVED_TASKS
)

classification_default_instruction_ru = """<div>
 Определите, какое животное на фотографии
</div>
"""

classification_default_instruction_en = """<div>
 Identify the animal in the photo
</div>
"""

classification_expert_task_instruction_ru = """<h1>
 Инструкция для исполнителей
</h1>
<div>
 Определите, какое животное на фотографии
</div>
<div>
 <input class="hide" id="hd-101" type="checkbox"/>
 <label for="hd-101">
  <strong>
   Экспертная разметка
  </strong>
 </label>
 <div>
  <h1>
   Цель задания
  </h1>
  <p>
   Ваша цель – быть посредником между заказчиком и исполнителями, предоставляя двусторонние гарантии:
  </p>
  <ul>
   <li>
    Для исполнителей – гарантия предоставления четко поставленной задачи.
   </li>
   <li>
    Для заказчика – гарантия предоставления качественных решений.
   </li>
  </ul>
  <p>
   <strong>
    Объект
   </strong>
   – проверяемое вами задание или задание с решением (далее просто
   <em>
    решение
   </em>
   ).
  </p>
  <p>
   <strong>
    Источник объекта
   </strong>
   – заказчик или исполнитель.
  </p>
  <p>
   Объекты, их источники, а также необходимые действия, определяются
   <strong>
    сценарием
   </strong>
   , указанным в
        карточке выполняемого вами задания.
  </p>
  <h1>
   Разметка объектов
  </h1>
  <p>
   Интерфейс предлагаемых вам заданий всегда построен одинаковым образом: сначала следует интерфейс
   <em>
    объекта
   </em>
   , затем фиксированная часть с его экспертной разметкой, отделяемая горизонтальной чертой.
  </p>
  <p>
   Интерфейс
   <em>
    объекта
   </em>
   зависит от решаемой заказчиком задачи. Например, если он решает задачу
   <em>
    классификация животных на фотографиях
   </em>
   , то интерфейс целиком может выглядеть так:
  </p>
  <div>
   <input class="hide" id="hd-30" type="checkbox"/>
   <label for="hd-30">
    <strong>
     Пример
     <em>
      объекта
     </em>
     -задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <div>
   <input class="hide" id="hd-31" type="checkbox"/>
   <label for="hd-31">
    <strong>
     Пример
     <em>
      объекта
     </em>
     -решения
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Разметка
   <em>
    объекта
   </em>
   включает в себя 2 пункта:
  </p>
  <ul>
   <li>
    Бинарная оценка
    <code>
     OK
    </code>
    :
    <em>
     Да
    </em>
    /
    <em>
     Нет
    </em>
    .
   </li>
   <li>
    Текстовый комментарий
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <p>
   Способ заполнения пунктов
   <code>
    OK
   </code>
   и
   <code>
    COMMENT
   </code>
   зависит от
   <em>
    сценария
   </em>
   .
  </p>
  <h1>
   Сценарии
  </h1>
  <h2>
   Проверка заданий заказчика
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка заданий)
   </em>
   в названии и примечанием
   <em>
    Проверка заданий
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-32" type="checkbox"/>
   <label for="hd-32">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Не все заказчики хорошо понимают, как лучше составлять инструкцию и интерфейс заданий так, чтобы исполнители
        четко понимали поставленное задание и не испытывали трудностей при решении.
  </p>
  <p>
   Даже при наличии хорошо составленной инструкции, размечаемые данные могут не соответствовать написанному в
        инструкции.
  </p>
  <p>
   Перечислим критерии хорошо сформулированного задания:
  </p>
  <ul>
   <li>
    <u>
     Полнота
    </u>
    – в инструкции перечислены все случаи, наблюдаемые в потоке размечаемых данных.
   </li>
   <li>
    <u>
     Понятность
    </u>
    – инструкция написана простым и понятным языком.
   </li>
   <li>
    <u>
     Непротиворечивость
    </u>
    – в инструкции нет пунктов, которые противоречат друг другу.
   </li>
   <li>
    <u>
     Краткость
    </u>
    – инструкция содержит минимум информации, нужный для объяснения сути задания.
   </li>
   <li>
    <u>
     Удобство
    </u>
    – интерфейс заданий удобен и предполагает минимум действий для решения задания.
   </li>
  </ul>
  <p>
   Вам будут показаны задания заказчика. Цель данного сценария:
  </p>
  <ul>
   <li>
    Дать обратную связь заказчику при необходимости доработать задания. Обратная связь бывает:
    <ul>
     <li>
      <u>
       По-
       <em>
        объектная
       </em>
      </u>
      , которую вы укажете при разметке объекта.
     </li>
     <li>
      <u>
       Общая
      </u>
      , которую вы можете сообщить в чате с заказчиком.
     </li>
    </ul>
   </li>
   <li>
    Сформировать набор обучающих заданий, который должен соответствовать следующим критериям:
    <ul>
     <li>
      <u>
       Полнота
      </u>
      – покрытие всех случаев из инструкции, при условии наличия соответствующих
                    примеров.
     </li>
     <li>
      <u>
       Содержательность
      </u>
      – примерно одинаковое количество информации для каждого случая. Чем
                    сложнее случай, тем больше обучающих примеров может потребоваться для необходимого количества
                    информации.
     </li>
    </ul>
   </li>
  </ul>
  <p>
   Для каждого задания вам требуется:
  </p>
  <ul>
   <li>
    Решить задание, как это сделал бы исполнитель согласно инструкции.
   </li>
   <li>
    Если задание
    <strong>
     некорректное
    </strong>
    – соответствующий случай не описан в инструкции, оно вообще
            не соответствует инструкции, возникли технические сложности вроде ошибки 404, либо по какой-то иной
            причине, выберите
    <code>
     Нет
    </code>
    в поле
    <code>
     OK
    </code>
    и укажите
    <code>
     COMMENT
    </code>
    с описанием
            проблемы.
   </li>
   <li>
    Если вышеперечисленных проблем нет, то задание
    <strong>
     корректное
    </strong>
    , выберите
    <code>
     Да
    </code>
    в поле
    <code>
     OK
    </code>
    . Если вы  считаете, что задание должно попасть в обучение, укажите
    <code>
     COMMENT
    </code>
    ,
            исполнители с ним смогут ознакомиться при прохождении обучения. В противном случае, оставьте
    <code>
     COMMENT
    </code>
    пустым.
   </li>
  </ul>
  <h2>
   Проверка решенных заданий заказчика
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка решений)
   </em>
   в названии и примечанием
   <em>
    Проверка заданий
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-33" type="checkbox"/>
   <label for="hd-33">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Сценарий эквивалентен предыдущему, с тем лишь отличием, что заказчик предоставляет задания с решениями.
  </p>
  <p>
   Правила разметки
   <em>
    объектов
   </em>
   (решений) немного изменятся. Решение
   <em>
    некорректное
   </em>
   , если:
  </p>
  <ul>
   <li>
    Некорректно задание (см. выше критерии и соответствующие действия)
   </li>
   <li>
    Некорректно решение – оно не соответствует инструкции, выберите
    <code>
     Нет
    </code>
    в поле
    <code>
     OK
    </code>
    и укажите
            причину в
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <h2>
   Проверка качества разметки
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка решений)
   </em>
   в названии и примечанием
   <em>
    Проверка качества разметки
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-34" type="checkbox"/>
   <label for="hd-34">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="verification-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="verification-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Сценарий эквивалентен предыдущему. Источник решений в данном сценарии – разметка исполнителей. Оценивать нужно только правильность решения.
  </p>
  <p>
   Решение
   <em>
    некорректное
   </em>
   , если оно не соответствует инструкции, выберите
   <code>
    Нет
   </code>
   в поле
   <code>
    OK
   </code>
   и опционально укажите причину в
   <code>
    COMMENT
   </code>
   .
  </p>
 </div>
</div>"""  # noqa

classification_expert_task_instruction_en = """<h1>
 Instructions for workers
</h1>
<div>
 Identify the animal in the photo
</div>
<div>
 <input class="hide" id="hd-101" type="checkbox"/>
 <label for="hd-101">
  <strong>
   Expert labeling
  </strong>
 </label>
 <div>
  <h1>
   Task purpose
  </h1>
  <p>
   Your goal is to be an intermediary between the customer and the workers, providing bilateral guarantees:
  </p>
  <ul>
   <li>
    For performers, it is a guarantee of providing a clearly defined task.
   </li>
   <li>
    For the customer – a guarantee of providing quality solutions.
   </li>
  </ul>
  <p>
   <strong>
    Object
   </strong>
   – the task or the task with the solution (next, just a
   <em>
    solution
   </em>
   ) you are checking.
  </p>
  <p>
   <strong>
    Object source
   </strong>
   – customer or worker.
  </p>
  <p>
   The objects, their sources, as well as the necessary actions are determined by the
   <strong>
    scenario
   </strong>
   specified in the card of the task you are performing.
  </p>
  <h1>
   Objects labeling
  </h1>
  <p>
   The interface of the tasks offered to you is always built in the same way: the interface follows first of the
   <em>
    object
   </em>
   , then the fixed part with its expert labeling, separated by a horizontal line.
  </p>
  <p>
   The interface of the
   <em>
    object
   </em>
   depends on the task being solved by the customer. For example, if he
        solves a problem
   <em>
    classification of animals in photos
   </em>
   , then the entire interface may look like this:
  </p>
  <div>
   <input class="hide" id="hd-30" type="checkbox"/>
   <label for="hd-30">
    <strong>
     Task
     <em>
      object
     </em>
     example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <div>
   <input class="hide" id="hd-31" type="checkbox"/>
   <label for="hd-31">
    <strong>
     Solution
     <em>
      object
     </em>
     example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   <em>
    Object
   </em>
   labeling includes 2 items:
  </p>
  <ul>
   <li>
    Binary evaluation
    <code>
     OK
    </code>
    :
    <em>
     Yes
    </em>
    /
    <em>
     No
    </em>
    .
   </li>
   <li>
    Textual comment
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <p>
   The way to fill in these items depends on the
   <em>
    scenario
   </em>
   .
  </p>
  <h1>
   Scenarios
  </h1>
  <h2>
   Checking the customer's tasks
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (task labeling)
   </em>
   in the title and the note
   <em>
    Task verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-32" type="checkbox"/>
   <label for="hd-32">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Not all customers understand well how best to compile instructions and the interface of tasks so that workers
        clearly understand the task and had no difficulties in performing it.
  </p>
  <p>
   Let's list the criteria for a well-formulated task:
  </p>
  <ul>
   <li>
    <u>
     Completeness
    </u>
    - the instructions list all the cases observed in the data stream.
   </li>
   <li>
    <u>
     Clarity
    </u>
    - the instruction is written in a simple and understandable language.
   </li>
   <li>
    <u>
     Consistency
    </u>
    – there are no points in the instructions that contradict each other.
   </li>
   <li>
    <u>
     Brevity
    </u>
    - the instruction contains a minimum of information necessary to explain the essence of the
            task.
   </li>
   <li>
    <u>
     Convenience
    </u>
    - the task interface is convenient and involves a minimum of actions to perform the
            task.
   </li>
  </ul>
  <p>
   You will be shown the customer's tasks. The purpose of this scenario:
  </p>
  <ul>
   <li>
    Give feedback to the customer, if necessary, to rework the tasks. Types of feedback are:
    <ul>
     <li>
      <u>
       By-
       <em>
        object
       </em>
      </u>
      , which you specify when labeling the object.
     </li>
     <li>
      <u>
       General
      </u>
      , which you can inform in a chat with the customer.
     </li>
    </ul>
   </li>
   <li>
    Create a set of training tasks that must meet the following criteria:
    <ul>
     <li>
      <u>
       Completeness
      </u>
      - coverage of all cases from the instructions, subject to the availability of
                    appropriate examples.
     </li>
     <li>
      <u>
       Informativeness
      </u>
      – approximately the same amount of information for each case. The more
                    complicated the case, the more training examples may be required for the required amount of
                    information.
     </li>
    </ul>
   </li>
  </ul>
  <p>
   For each task you need:
  </p>
  <ul>
   <li>
    Complete the task as the worker would do according to the instructions.
   </li>
   <li>
    Perform the task as the worker would do according to the instructions.
   </li>
   <li>
    If the task is
    <strong>
     incorrect
    </strong>
    - the corresponding case is not described in the instructions, it
            is generally does not comply with the instructions, there were technical difficulties like error 404, or
            for some other reason, choose
    <code>
     No
    </code>
    in
    <code>
     OK
    </code>
    field and specify
    <code>
     COMMENT
    </code>
    with a problems description.
   </li>
   <li>
    If there are no problems listed above, then the task is
    <strong>
     correct
    </strong>
    , choose
    <code>
     Yes
    </code>
    in
    <code>
     OK
    </code>
    field. If you  think that the task should be
            included in the training, specify
    <code>
     COMMENT
    </code>
    , which workers will be able to learn during
            training. Otherwise, leave
    <code>
     COMMENT
    </code>
    empty.
   </li>
  </ul>
  <h2>
   Checking the customer's solved tasks
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (solution labeling)
   </em>
   in the title and the note
   <em>
    Task verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-33" type="checkbox"/>
   <label for="hd-33">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   The scenario is equivalent to the previous one, with the only difference that the customer provides tasks with
        solutions.
  </p>
  <p>
   The rules for labeling of
   <em>
    objects
   </em>
   (solutions) will change slightly. The solution is
   <em>
    incorrect
   </em>
   if:
  </p>
  <ul>
   <li>
    The task is incorrect (see the criteria and corresponding actions above)
   </li>
   <li>
    The solution is incorrect – it does not comply with the instructions, choose
    <code>
     No
    </code>
    in
    <code>
     OK
    </code>
    field and specify the reason in
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <h2>
   Labeling quality verification
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (solution labeling)
   </em>
   in the title and the note
   <em>
    Labeling quality verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-34" type="checkbox"/>
   <label for="hd-34">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   The scenario is equivalent to the previous one. In this scenario tasks were solved by workers. You should only evaluate the correctness of the
   <strong>
    solution
   </strong>
  </p>
  <p>
   The solution is
   <em>
    incorrect
   </em>
   if it does not comply with the instructions, choose
   <code>
    No
   </code>
   in
   <code>
    OK
   </code>
   field and specify the reason in
   <code>
    COMMENT
   </code>
   .
  </p>
 </div>
</div>"""  # noqa

classification_expert_solution_instruction_ru = """<h1>
 Инструкция для исполнителей
</h1>
<div>
 Определите, какое животное на фотографии
</div>
<div>
 <input class="hide" id="hd-101" type="checkbox"/>
 <label for="hd-101">
  <strong>
   Экспертная разметка
  </strong>
 </label>
 <div>
  <h1>
   Цель задания
  </h1>
  <p>
   Ваша цель – быть посредником между заказчиком и исполнителями, предоставляя двусторонние гарантии:
  </p>
  <ul>
   <li>
    Для исполнителей – гарантия предоставления четко поставленной задачи.
   </li>
   <li>
    Для заказчика – гарантия предоставления качественных решений.
   </li>
  </ul>
  <p>
   <strong>
    Объект
   </strong>
   – проверяемое вами задание или задание с решением (далее просто
   <em>
    решение
   </em>
   ).
  </p>
  <p>
   <strong>
    Источник объекта
   </strong>
   – заказчик или исполнитель.
  </p>
  <p>
   Объекты, их источники, а также необходимые действия, определяются
   <strong>
    сценарием
   </strong>
   , указанным в
        карточке выполняемого вами задания.
  </p>
  <h1>
   Разметка объектов
  </h1>
  <p>
   Интерфейс предлагаемых вам заданий всегда построен одинаковым образом: сначала следует интерфейс
   <em>
    объекта
   </em>
   , затем фиксированная часть с его экспертной разметкой, отделяемая горизонтальной чертой.
  </p>
  <p>
   Интерфейс
   <em>
    объекта
   </em>
   зависит от решаемой заказчиком задачи. Например, если он решает задачу
   <em>
    классификация животных на фотографиях
   </em>
   , то интерфейс целиком может выглядеть так:
  </p>
  <div>
   <input class="hide" id="hd-30" type="checkbox"/>
   <label for="hd-30">
    <strong>
     Пример
     <em>
      объекта
     </em>
     -задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <div>
   <input class="hide" id="hd-31" type="checkbox"/>
   <label for="hd-31">
    <strong>
     Пример
     <em>
      объекта
     </em>
     -решения
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Разметка
   <em>
    объекта
   </em>
   включает в себя 2 пункта:
  </p>
  <ul>
   <li>
    Бинарная оценка
    <code>
     OK
    </code>
    :
    <em>
     Да
    </em>
    /
    <em>
     Нет
    </em>
    .
   </li>
   <li>
    Текстовый комментарий
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <p>
   Способ заполнения пунктов
   <code>
    OK
   </code>
   и
   <code>
    COMMENT
   </code>
   зависит от
   <em>
    сценария
   </em>
   .
  </p>
  <h1>
   Сценарии
  </h1>
  <h2>
   Проверка заданий заказчика
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка заданий)
   </em>
   в названии и примечанием
   <em>
    Проверка заданий
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-32" type="checkbox"/>
   <label for="hd-32">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Не все заказчики хорошо понимают, как лучше составлять инструкцию и интерфейс заданий так, чтобы исполнители
        четко понимали поставленное задание и не испытывали трудностей при решении.
  </p>
  <p>
   Даже при наличии хорошо составленной инструкции, размечаемые данные могут не соответствовать написанному в
        инструкции.
  </p>
  <p>
   Перечислим критерии хорошо сформулированного задания:
  </p>
  <ul>
   <li>
    <u>
     Полнота
    </u>
    – в инструкции перечислены все случаи, наблюдаемые в потоке размечаемых данных.
   </li>
   <li>
    <u>
     Понятность
    </u>
    – инструкция написана простым и понятным языком.
   </li>
   <li>
    <u>
     Непротиворечивость
    </u>
    – в инструкции нет пунктов, которые противоречат друг другу.
   </li>
   <li>
    <u>
     Краткость
    </u>
    – инструкция содержит минимум информации, нужный для объяснения сути задания.
   </li>
   <li>
    <u>
     Удобство
    </u>
    – интерфейс заданий удобен и предполагает минимум действий для решения задания.
   </li>
  </ul>
  <p>
   Вам будут показаны задания заказчика. Цель данного сценария:
  </p>
  <ul>
   <li>
    Дать обратную связь заказчику при необходимости доработать задания. Обратная связь бывает:
    <ul>
     <li>
      <u>
       По-
       <em>
        объектная
       </em>
      </u>
      , которую вы укажете при разметке объекта.
     </li>
     <li>
      <u>
       Общая
      </u>
      , которую вы можете сообщить в чате с заказчиком.
     </li>
    </ul>
   </li>
   <li>
    Сформировать набор обучающих заданий, который должен соответствовать следующим критериям:
    <ul>
     <li>
      <u>
       Полнота
      </u>
      – покрытие всех случаев из инструкции, при условии наличия соответствующих
                    примеров.
     </li>
     <li>
      <u>
       Содержательность
      </u>
      – примерно одинаковое количество информации для каждого случая. Чем
                    сложнее случай, тем больше обучающих примеров может потребоваться для необходимого количества
                    информации.
     </li>
    </ul>
   </li>
  </ul>
  <p>
   Для каждого задания вам требуется:
  </p>
  <ul>
   <li>
    Решить задание, как это сделал бы исполнитель согласно инструкции.
   </li>
   <li>
    Если задание
    <strong>
     некорректное
    </strong>
    – соответствующий случай не описан в инструкции, оно вообще
            не соответствует инструкции, возникли технические сложности вроде ошибки 404, либо по какой-то иной
            причине, выберите
    <code>
     Нет
    </code>
    в поле
    <code>
     OK
    </code>
    и укажите
    <code>
     COMMENT
    </code>
    с описанием
            проблемы.
   </li>
   <li>
    Если вышеперечисленных проблем нет, то задание
    <strong>
     корректное
    </strong>
    , выберите
    <code>
     Да
    </code>
    в поле
    <code>
     OK
    </code>
    . Если вы  считаете, что задание должно попасть в обучение, укажите
    <code>
     COMMENT
    </code>
    ,
            исполнители с ним смогут ознакомиться при прохождении обучения. В противном случае, оставьте
    <code>
     COMMENT
    </code>
    пустым.
   </li>
  </ul>
  <h2>
   Проверка решенных заданий заказчика
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка решений)
   </em>
   в названии и примечанием
   <em>
    Проверка заданий
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-33" type="checkbox"/>
   <label for="hd-33">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Сценарий эквивалентен предыдущему, с тем лишь отличием, что заказчик предоставляет задания с решениями.
  </p>
  <p>
   Правила разметки
   <em>
    объектов
   </em>
   (решений) немного изменятся. Решение
   <em>
    некорректное
   </em>
   , если:
  </p>
  <ul>
   <li>
    Некорректно задание (см. выше критерии и соответствующие действия)
   </li>
   <li>
    Некорректно решение – оно не соответствует инструкции, выберите
    <code>
     Нет
    </code>
    в поле
    <code>
     OK
    </code>
    и укажите
            причину в
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <h2>
   Проверка качества разметки
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка решений)
   </em>
   в названии и примечанием
   <em>
    Проверка качества разметки
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-34" type="checkbox"/>
   <label for="hd-34">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="verification-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="verification-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Сценарий эквивалентен предыдущему. Источник решений в данном сценарии – разметка исполнителей. Оценивать нужно только правильность решения.
  </p>
  <p>
   Решение
   <em>
    некорректное
   </em>
   , если оно не соответствует инструкции, выберите
   <code>
    Нет
   </code>
   в поле
   <code>
    OK
   </code>
   и опционально укажите причину в
   <code>
    COMMENT
   </code>
   .
  </p>
 </div>
</div>"""  # noqa

classification_expert_solution_instruction_en = """<h1>
 Instructions for workers
</h1>
<div>
 Identify the animal in the photo
</div>
<div>
 <input class="hide" id="hd-101" type="checkbox"/>
 <label for="hd-101">
  <strong>
   Expert labeling
  </strong>
 </label>
 <div>
  <h1>
   Task purpose
  </h1>
  <p>
   Your goal is to be an intermediary between the customer and the workers, providing bilateral guarantees:
  </p>
  <ul>
   <li>
    For performers, it is a guarantee of providing a clearly defined task.
   </li>
   <li>
    For the customer – a guarantee of providing quality solutions.
   </li>
  </ul>
  <p>
   <strong>
    Object
   </strong>
   – the task or the task with the solution (next, just a
   <em>
    solution
   </em>
   ) you are checking.
  </p>
  <p>
   <strong>
    Object source
   </strong>
   – customer or worker.
  </p>
  <p>
   The objects, their sources, as well as the necessary actions are determined by the
   <strong>
    scenario
   </strong>
   specified in the card of the task you are performing.
  </p>
  <h1>
   Objects labeling
  </h1>
  <p>
   The interface of the tasks offered to you is always built in the same way: the interface follows first of the
   <em>
    object
   </em>
   , then the fixed part with its expert labeling, separated by a horizontal line.
  </p>
  <p>
   The interface of the
   <em>
    object
   </em>
   depends on the task being solved by the customer. For example, if he
        solves a problem
   <em>
    classification of animals in photos
   </em>
   , then the entire interface may look like this:
  </p>
  <div>
   <input class="hide" id="hd-30" type="checkbox"/>
   <label for="hd-30">
    <strong>
     Task
     <em>
      object
     </em>
     example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <div>
   <input class="hide" id="hd-31" type="checkbox"/>
   <label for="hd-31">
    <strong>
     Solution
     <em>
      object
     </em>
     example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   <em>
    Object
   </em>
   labeling includes 2 items:
  </p>
  <ul>
   <li>
    Binary evaluation
    <code>
     OK
    </code>
    :
    <em>
     Yes
    </em>
    /
    <em>
     No
    </em>
    .
   </li>
   <li>
    Textual comment
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <p>
   The way to fill in these items depends on the
   <em>
    scenario
   </em>
   .
  </p>
  <h1>
   Scenarios
  </h1>
  <h2>
   Checking the customer's tasks
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (task labeling)
   </em>
   in the title and the note
   <em>
    Task verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-32" type="checkbox"/>
   <label for="hd-32">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Not all customers understand well how best to compile instructions and the interface of tasks so that workers
        clearly understand the task and had no difficulties in performing it.
  </p>
  <p>
   Let's list the criteria for a well-formulated task:
  </p>
  <ul>
   <li>
    <u>
     Completeness
    </u>
    - the instructions list all the cases observed in the data stream.
   </li>
   <li>
    <u>
     Clarity
    </u>
    - the instruction is written in a simple and understandable language.
   </li>
   <li>
    <u>
     Consistency
    </u>
    – there are no points in the instructions that contradict each other.
   </li>
   <li>
    <u>
     Brevity
    </u>
    - the instruction contains a minimum of information necessary to explain the essence of the
            task.
   </li>
   <li>
    <u>
     Convenience
    </u>
    - the task interface is convenient and involves a minimum of actions to perform the
            task.
   </li>
  </ul>
  <p>
   You will be shown the customer's tasks. The purpose of this scenario:
  </p>
  <ul>
   <li>
    Give feedback to the customer, if necessary, to rework the tasks. Types of feedback are:
    <ul>
     <li>
      <u>
       By-
       <em>
        object
       </em>
      </u>
      , which you specify when labeling the object.
     </li>
     <li>
      <u>
       General
      </u>
      , which you can inform in a chat with the customer.
     </li>
    </ul>
   </li>
   <li>
    Create a set of training tasks that must meet the following criteria:
    <ul>
     <li>
      <u>
       Completeness
      </u>
      - coverage of all cases from the instructions, subject to the availability of
                    appropriate examples.
     </li>
     <li>
      <u>
       Informativeness
      </u>
      – approximately the same amount of information for each case. The more
                    complicated the case, the more training examples may be required for the required amount of
                    information.
     </li>
    </ul>
   </li>
  </ul>
  <p>
   For each task you need:
  </p>
  <ul>
   <li>
    Complete the task as the worker would do according to the instructions.
   </li>
   <li>
    Perform the task as the worker would do according to the instructions.
   </li>
   <li>
    If the task is
    <strong>
     incorrect
    </strong>
    - the corresponding case is not described in the instructions, it
            is generally does not comply with the instructions, there were technical difficulties like error 404, or
            for some other reason, choose
    <code>
     No
    </code>
    in
    <code>
     OK
    </code>
    field and specify
    <code>
     COMMENT
    </code>
    with a problems description.
   </li>
   <li>
    If there are no problems listed above, then the task is
    <strong>
     correct
    </strong>
    , choose
    <code>
     Yes
    </code>
    in
    <code>
     OK
    </code>
    field. If you  think that the task should be
            included in the training, specify
    <code>
     COMMENT
    </code>
    , which workers will be able to learn during
            training. Otherwise, leave
    <code>
     COMMENT
    </code>
    empty.
   </li>
  </ul>
  <h2>
   Checking the customer's solved tasks
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (solution labeling)
   </em>
   in the title and the note
   <em>
    Task verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-33" type="checkbox"/>
   <label for="hd-33">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   The scenario is equivalent to the previous one, with the only difference that the customer provides tasks with
        solutions.
  </p>
  <p>
   The rules for labeling of
   <em>
    objects
   </em>
   (solutions) will change slightly. The solution is
   <em>
    incorrect
   </em>
   if:
  </p>
  <ul>
   <li>
    The task is incorrect (see the criteria and corresponding actions above)
   </li>
   <li>
    The solution is incorrect – it does not comply with the instructions, choose
    <code>
     No
    </code>
    in
    <code>
     OK
    </code>
    field and specify the reason in
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <h2>
   Labeling quality verification
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (solution labeling)
   </em>
   in the title and the note
   <em>
    Labeling quality verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-34" type="checkbox"/>
   <label for="hd-34">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   The scenario is equivalent to the previous one. In this scenario tasks were solved by workers. You should only evaluate the correctness of the
   <strong>
    solution
   </strong>
  </p>
  <p>
   The solution is
   <em>
    incorrect
   </em>
   if it does not comply with the instructions, choose
   <code>
    No
   </code>
   in
   <code>
    OK
   </code>
   field and specify the reason in
   <code>
    COMMENT
   </code>
   .
  </p>
 </div>
</div>"""  # noqa

annotation_default_instruction_ru = """<div>
 Запишите звучащие на аудио слова
</div>
"""

annotation_default_instruction_en = """<div>
 Transcribe the audio
</div>
"""

annotation_expert_task_instruction_ru = """<h1>
 Инструкция для исполнителей
</h1>
<div>
 Запишите звучащие на аудио слова
</div>
<div>
 <input class="hide" id="hd-101" type="checkbox"/>
 <label for="hd-101">
  <strong>
   Экспертная разметка
  </strong>
 </label>
 <div>
  <h1>
   Цель задания
  </h1>
  <p>
   Ваша цель – быть посредником между заказчиком и исполнителями, предоставляя двусторонние гарантии:
  </p>
  <ul>
   <li>
    Для исполнителей – гарантия предоставления четко поставленной задачи.
   </li>
   <li>
    Для заказчика – гарантия предоставления качественных решений.
   </li>
  </ul>
  <p>
   <strong>
    Объект
   </strong>
   – проверяемое вами задание или задание с решением (далее просто
   <em>
    решение
   </em>
   ).
  </p>
  <p>
   <strong>
    Источник объекта
   </strong>
   – заказчик или исполнитель.
  </p>
  <p>
   Объекты, их источники, а также необходимые действия, определяются
   <strong>
    сценарием
   </strong>
   , указанным в
        карточке выполняемого вами задания.
  </p>
  <h1>
   Разметка объектов
  </h1>
  <p>
   Интерфейс предлагаемых вам заданий всегда построен одинаковым образом: сначала следует интерфейс
   <em>
    объекта
   </em>
   , затем фиксированная часть с его экспертной разметкой, отделяемая горизонтальной чертой.
  </p>
  <p>
   Интерфейс
   <em>
    объекта
   </em>
   зависит от решаемой заказчиком задачи. Например, если он решает задачу
   <em>
    расшифровка речи из аудиозаписей
   </em>
   , то интерфейс целиком может выглядеть так:
  </p>
  <div>
   <input class="hide" id="hd-30" type="checkbox"/>
   <label for="hd-30">
    <strong>
     Пример
     <em>
      объекта
     </em>
     -задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <div>
   <input class="hide" id="hd-31" type="checkbox"/>
   <label for="hd-31">
    <strong>
     Пример
     <em>
      объекта
     </em>
     -решения
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Разметка
   <em>
    объекта
   </em>
   включает в себя 3 пункта:
  </p>
  <ul>
   <li>
    Бинарная оценка решения
    <code>
     EVAL
    </code>
    :
    <code>
     Да
    </code>
    /
    <code>
     Нет
    </code>
    . Этот пункт всегда должен
отражать, правильно ли в соответствии с инструкцией по аннотации выполнено исходное задание.
   </li>
   <li>
    Бинарная оценка
    <code>
     OK
    </code>
    :
    <em>
     Да
    </em>
    /
    <em>
     Нет
    </em>
    .
   </li>
   <li>
    Текстовый комментарий
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <p>
   Способ заполнения пунктов
   <code>
    OK
   </code>
   и
   <code>
    COMMENT
   </code>
   зависит от
   <em>
    сценария
   </em>
   .
  </p>
  <h1>
   Сценарии
  </h1>
  <h2>
   Проверка заданий заказчика
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка заданий)
   </em>
   в названии и примечанием
   <em>
    Проверка заданий
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-32" type="checkbox"/>
   <label for="hd-32">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Не все заказчики хорошо понимают, как лучше составлять инструкцию и интерфейс заданий так, чтобы исполнители
        четко понимали поставленное задание и не испытывали трудностей при решении.
  </p>
  <p>
   Даже при наличии хорошо составленной инструкции, размечаемые данные могут не соответствовать написанному в
        инструкции.
  </p>
  <p>
   Перечислим критерии хорошо сформулированного задания:
  </p>
  <ul>
   <li>
    <u>
     Полнота
    </u>
    – в инструкции перечислены все случаи, наблюдаемые в потоке размечаемых данных.
   </li>
   <li>
    <u>
     Понятность
    </u>
    – инструкция написана простым и понятным языком.
   </li>
   <li>
    <u>
     Непротиворечивость
    </u>
    – в инструкции нет пунктов, которые противоречат друг другу.
   </li>
   <li>
    <u>
     Краткость
    </u>
    – инструкция содержит минимум информации, нужный для объяснения сути задания.
   </li>
   <li>
    <u>
     Удобство
    </u>
    – интерфейс заданий удобен и предполагает минимум действий для решения задания.
   </li>
  </ul>
  <p>
   Вам будут показаны задания заказчика. Цель данного сценария:
  </p>
  <ul>
   <li>
    Дать обратную связь заказчику при необходимости доработать задания. Обратная связь бывает:
    <ul>
     <li>
      <u>
       По-
       <em>
        объектная
       </em>
      </u>
      , которую вы укажете при разметке объекта.
     </li>
     <li>
      <u>
       Общая
      </u>
      , которую вы можете сообщить в чате с заказчиком.
     </li>
    </ul>
   </li>
   <li>
    Сформировать набор обучающих заданий, который должен соответствовать следующим критериям:
    <ul>
     <li>
      <u>
       Полнота
      </u>
      – покрытие всех случаев из инструкции, при условии наличия соответствующих
                    примеров.
     </li>
     <li>
      <u>
       Содержательность
      </u>
      – примерно одинаковое количество информации для каждого случая. Чем
                    сложнее случай, тем больше обучающих примеров может потребоваться для необходимого количества
                    информации.
     </li>
    </ul>
   </li>
  </ul>
  <p>
   Для каждого задания вам требуется:
  </p>
  <ul>
   <li>
    Решить задание, либо правильно – как это сделал бы исполнитель согласно инструкции, либо специально неправильно –
допустите ошибку, нарушив один из важных пунктов инструкции.
   </li>
   <li>
    В поле
    <code>
     EVAL
    </code>
    соответственно выберите, правильно выполнили задание или нет.
   </li>
   <li>
    Если задание
    <strong>
     некорректное
    </strong>
    – соответствующий случай не описан в инструкции, оно вообще
            не соответствует инструкции, возникли технические сложности вроде ошибки 404, либо по какой-то иной
            причине, выберите
    <code>
     Нет
    </code>
    в поле
    <code>
     OK
    </code>
    и укажите
    <code>
     COMMENT
    </code>
    с описанием
            проблемы.
   </li>
   <li>
    Если вышеперечисленных проблем нет, то задание
    <strong>
     корректное
    </strong>
    , выберите
    <code>
     Да
    </code>
    в поле
    <code>
     OK
    </code>
    . Если вы допустили при выполнении задания специальную ошибку или считаете, что задание должно попасть в обучение, укажите
    <code>
     COMMENT
    </code>
    ,
            исполнители с ним смогут ознакомиться при прохождении обучения. В противном случае, оставьте
    <code>
     COMMENT
    </code>
    пустым.
   </li>
  </ul>
  <h2>
   Проверка решенных заданий заказчика
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    проверка (разметка решений)
   </em>
   в названии и примечанием
   <em>
    Проверка заданий
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-33" type="checkbox"/>
   <label for="hd-33">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Сценарий эквивалентен предыдущему, с тем лишь отличием, что заказчик предоставляет задания с решениями. В поле
   <code>
    EVAL
   </code>
   выберите, верно выполнено задание или нет.
  </p>
  <p>
   Правила разметки
   <em>
    объектов
   </em>
   (решений) немного изменятся. Решение
   <em>
    некорректное
   </em>
   , если:
  </p>
  <ul>
   <li>
    Некорректно задание (см. выше критерии и соответствующие действия)
   </li>
   <li>
    Некорректно решение – оно не соответствует инструкции, выберите
    <code>
     Нет
    </code>
    в поле
    <code>
     OK
    </code>
    и укажите
            причину в
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <h2>
   Проверка качества разметки
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка решений)
   </em>
   в названии и примечанием
   <em>
    Проверка качества разметки
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-34" type="checkbox"/>
   <label for="hd-34">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="verification-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="verification-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Сценарий эквивалентен предыдущему. Источник решений в данном сценарии – разметка исполнителей. Оценивать нужно только правильность решения.
  </p>
  <p>
   Решение
   <em>
    некорректное
   </em>
   , если оно не соответствует инструкции, выберите
   <code>
    Нет
   </code>
   в поле
   <code>
    OK
   </code>
   и опционально укажите причину в
   <code>
    COMMENT
   </code>
   .
  </p>
 </div>
</div>"""  # noqa

annotation_expert_task_instruction_en = """<h1>
 Instructions for workers
</h1>
<div>
 Transcribe the audio
</div>
<div>
 <input class="hide" id="hd-101" type="checkbox"/>
 <label for="hd-101">
  <strong>
   Expert labeling
  </strong>
 </label>
 <div>
  <h1>
   Task purpose
  </h1>
  <p>
   Your goal is to be an intermediary between the customer and the workers, providing bilateral guarantees:
  </p>
  <ul>
   <li>
    For performers, it is a guarantee of providing a clearly defined task.
   </li>
   <li>
    For the customer – a guarantee of providing quality solutions.
   </li>
  </ul>
  <p>
   <strong>
    Object
   </strong>
   – the task or the task with the solution (next, just a
   <em>
    solution
   </em>
   ) you are checking.
  </p>
  <p>
   <strong>
    Object source
   </strong>
   – customer or worker.
  </p>
  <p>
   The objects, their sources, as well as the necessary actions are determined by the
   <strong>
    scenario
   </strong>
   specified in the card of the task you are performing.
  </p>
  <h1>
   Objects labeling
  </h1>
  <p>
   The interface of the tasks offered to you is always built in the same way: the interface follows first of the
   <em>
    object
   </em>
   , then the fixed part with its expert labeling, separated by a horizontal line.
  </p>
  <p>
   The interface of the
   <em>
    object
   </em>
   depends on the task being solved by the customer. For example, if he
        solves a problem
   <em>
    transcript of speech from audio
   </em>
   , then the entire interface may look like this:
  </p>
  <div>
   <input class="hide" id="hd-30" type="checkbox"/>
   <label for="hd-30">
    <strong>
     Task
     <em>
      object
     </em>
     example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <div>
   <input class="hide" id="hd-31" type="checkbox"/>
   <label for="hd-31">
    <strong>
     Solution
     <em>
      object
     </em>
     example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   <em>
    Object
   </em>
   labeling includes 3 items:
  </p>
  <ul>
   <li>
    Binary evaluation of solution
    <code>
     EVAL
    </code>
    :
    <code>
     Yes
    </code>
    /
    <code>
     No
    </code>
    . This option should always
reflect whether the annotation was done accurately according to the instruction or not.
   </li>
   <li>
    Binary evaluation
    <code>
     OK
    </code>
    :
    <em>
     Yes
    </em>
    /
    <em>
     No
    </em>
    .
   </li>
   <li>
    Textual comment
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <p>
   The way to fill in these items depends on the
   <em>
    scenario
   </em>
   .
  </p>
  <h1>
   Scenarios
  </h1>
  <h2>
   Checking the customer's tasks
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (task labeling)
   </em>
   in the title and the note
   <em>
    Task verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-32" type="checkbox"/>
   <label for="hd-32">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Not all customers understand well how best to compile instructions and the interface of tasks so that workers
        clearly understand the task and had no difficulties in performing it.
  </p>
  <p>
   Let's list the criteria for a well-formulated task:
  </p>
  <ul>
   <li>
    <u>
     Completeness
    </u>
    - the instructions list all the cases observed in the data stream.
   </li>
   <li>
    <u>
     Clarity
    </u>
    - the instruction is written in a simple and understandable language.
   </li>
   <li>
    <u>
     Consistency
    </u>
    – there are no points in the instructions that contradict each other.
   </li>
   <li>
    <u>
     Brevity
    </u>
    - the instruction contains a minimum of information necessary to explain the essence of the
            task.
   </li>
   <li>
    <u>
     Convenience
    </u>
    - the task interface is convenient and involves a minimum of actions to perform the
            task.
   </li>
  </ul>
  <p>
   You will be shown the customer's tasks. The purpose of this scenario:
  </p>
  <ul>
   <li>
    Give feedback to the customer, if necessary, to rework the tasks. Types of feedback are:
    <ul>
     <li>
      <u>
       By-
       <em>
        object
       </em>
      </u>
      , which you specify when labeling the object.
     </li>
     <li>
      <u>
       General
      </u>
      , which you can inform in a chat with the customer.
     </li>
    </ul>
   </li>
   <li>
    Create a set of training tasks that must meet the following criteria:
    <ul>
     <li>
      <u>
       Completeness
      </u>
      - coverage of all cases from the instructions, subject to the availability of
                    appropriate examples.
     </li>
     <li>
      <u>
       Informativeness
      </u>
      – approximately the same amount of information for each case. The more
                    complicated the case, the more training examples may be required for the required amount of
                    information.
     </li>
    </ul>
   </li>
  </ul>
  <p>
   For each task you need:
  </p>
  <ul>
   <li>
    Complete the task either accurately – as the worker would do according to the instructions, or make some errors on
purpose, violating one of the important points of the instructions.
   </li>
   <li>
    In
    <code>
     EVAL
    </code>
    field choose whether you completed the task accurately or not.
   </li>
   <li>
    Perform the task as the worker would do according to the instructions.
   </li>
   <li>
    If the task is
    <strong>
     incorrect
    </strong>
    - the corresponding case is not described in the instructions, it
            is generally does not comply with the instructions, there were technical difficulties like error 404, or
            for some other reason, choose
    <code>
     No
    </code>
    in
    <code>
     OK
    </code>
    field and specify
    <code>
     COMMENT
    </code>
    with a problems description.
   </li>
   <li>
    If there are no problems listed above, then the task is
    <strong>
     correct
    </strong>
    , choose
    <code>
     Yes
    </code>
    in
    <code>
     OK
    </code>
    field. If you made some errors on purpose while completing the task or think that the task should be
            included in the training, specify
    <code>
     COMMENT
    </code>
    , which workers will be able to learn during
            training. Otherwise, leave
    <code>
     COMMENT
    </code>
    empty.
   </li>
  </ul>
  <h2>
   Checking the customer's solved tasks
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    check (solution labeling)
   </em>
   in the title and the note
   <em>
    Task verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-33" type="checkbox"/>
   <label for="hd-33">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   The scenario is equivalent to the previous one, with the only difference that the customer provides tasks with
        solutions. In
   <code>
    EVAL
   </code>
   field choose, whether you've completed the task accurately or not.
  </p>
  <p>
   The rules for labeling of
   <em>
    objects
   </em>
   (solutions) will change slightly. The solution is
   <em>
    incorrect
   </em>
   if:
  </p>
  <ul>
   <li>
    The task is incorrect (see the criteria and corresponding actions above)
   </li>
   <li>
    The solution is incorrect – it does not comply with the instructions, choose
    <code>
     No
    </code>
    in
    <code>
     OK
    </code>
    field and specify the reason in
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <h2>
   Labeling quality verification
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (solution labeling)
   </em>
   in the title and the note
   <em>
    Labeling quality verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-34" type="checkbox"/>
   <label for="hd-34">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   The scenario is equivalent to the previous one. In this scenario tasks were solved by workers. You should only evaluate the correctness of the
   <strong>
    solution
   </strong>
  </p>
  <p>
   The solution is
   <em>
    incorrect
   </em>
   if it does not comply with the instructions, choose
   <code>
    No
   </code>
   in
   <code>
    OK
   </code>
   field and specify the reason in
   <code>
    COMMENT
   </code>
   .
  </p>
 </div>
</div>"""  # noqa

annotation_expert_solution_instruction_ru = """<h1>
 Инструкция для исполнителей
</h1>
<div>
 <div>
  <p>
   Вы увидите решения заданий, выполненные по инструкции ниже. Проверьте решения на соответствие инструкции.
  </p>
 </div>
 <h1>
  Инструкция, по которой выполнены решения
 </h1>
 <div>
  Запишите звучащие на аудио слова
 </div>
</div>
<div>
 <input class="hide" id="hd-101" type="checkbox"/>
 <label for="hd-101">
  <strong>
   Экспертная разметка
  </strong>
 </label>
 <div>
  <h1>
   Цель задания
  </h1>
  <p>
   Ваша цель – быть посредником между заказчиком и исполнителями, предоставляя двусторонние гарантии:
  </p>
  <ul>
   <li>
    Для исполнителей – гарантия предоставления четко поставленной задачи.
   </li>
   <li>
    Для заказчика – гарантия предоставления качественных решений.
   </li>
  </ul>
  <p>
   <strong>
    Объект
   </strong>
   – проверяемое вами задание или задание с решением (далее просто
   <em>
    решение
   </em>
   ).
  </p>
  <p>
   <strong>
    Источник объекта
   </strong>
   – заказчик или исполнитель.
  </p>
  <p>
   Объекты, их источники, а также необходимые действия, определяются
   <strong>
    сценарием
   </strong>
   , указанным в
        карточке выполняемого вами задания.
  </p>
  <h1>
   Разметка объектов
  </h1>
  <p>
   Интерфейс предлагаемых вам заданий всегда построен одинаковым образом: сначала следует интерфейс
   <em>
    объекта
   </em>
   , затем фиксированная часть с его экспертной разметкой, отделяемая горизонтальной чертой.
  </p>
  <p>
   Интерфейс
   <em>
    объекта
   </em>
   зависит от решаемой заказчиком задачи. Например, если он решает задачу
   <em>
    расшифровка речи из аудиозаписей
   </em>
   , то интерфейс целиком может выглядеть так:
  </p>
  <div>
   <input class="hide" id="hd-30" type="checkbox"/>
   <label for="hd-30">
    <strong>
     Пример
     <em>
      объекта
     </em>
     -задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <div>
   <input class="hide" id="hd-31" type="checkbox"/>
   <label for="hd-31">
    <strong>
     Пример
     <em>
      объекта
     </em>
     -решения
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Разметка
   <em>
    объекта
   </em>
   включает в себя 3 пункта:
  </p>
  <ul>
   <li>
    Бинарная оценка решения
    <code>
     EVAL
    </code>
    :
    <code>
     Да
    </code>
    /
    <code>
     Нет
    </code>
    . Этот пункт всегда должен
отражать, правильно ли в соответствии с инструкцией по аннотации выполнено исходное задание.
   </li>
   <li>
    Бинарная оценка
    <code>
     OK
    </code>
    :
    <em>
     Да
    </em>
    /
    <em>
     Нет
    </em>
    .
   </li>
   <li>
    Текстовый комментарий
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <p>
   Способ заполнения пунктов
   <code>
    OK
   </code>
   и
   <code>
    COMMENT
   </code>
   зависит от
   <em>
    сценария
   </em>
   .
  </p>
  <h1>
   Сценарии
  </h1>
  <h2>
   Проверка заданий заказчика
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка заданий)
   </em>
   в названии и примечанием
   <em>
    Проверка заданий
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-32" type="checkbox"/>
   <label for="hd-32">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Не все заказчики хорошо понимают, как лучше составлять инструкцию и интерфейс заданий так, чтобы исполнители
        четко понимали поставленное задание и не испытывали трудностей при решении.
  </p>
  <p>
   Даже при наличии хорошо составленной инструкции, размечаемые данные могут не соответствовать написанному в
        инструкции.
  </p>
  <p>
   Перечислим критерии хорошо сформулированного задания:
  </p>
  <ul>
   <li>
    <u>
     Полнота
    </u>
    – в инструкции перечислены все случаи, наблюдаемые в потоке размечаемых данных.
   </li>
   <li>
    <u>
     Понятность
    </u>
    – инструкция написана простым и понятным языком.
   </li>
   <li>
    <u>
     Непротиворечивость
    </u>
    – в инструкции нет пунктов, которые противоречат друг другу.
   </li>
   <li>
    <u>
     Краткость
    </u>
    – инструкция содержит минимум информации, нужный для объяснения сути задания.
   </li>
   <li>
    <u>
     Удобство
    </u>
    – интерфейс заданий удобен и предполагает минимум действий для решения задания.
   </li>
  </ul>
  <p>
   Вам будут показаны задания заказчика. Цель данного сценария:
  </p>
  <ul>
   <li>
    Дать обратную связь заказчику при необходимости доработать задания. Обратная связь бывает:
    <ul>
     <li>
      <u>
       По-
       <em>
        объектная
       </em>
      </u>
      , которую вы укажете при разметке объекта.
     </li>
     <li>
      <u>
       Общая
      </u>
      , которую вы можете сообщить в чате с заказчиком.
     </li>
    </ul>
   </li>
   <li>
    Сформировать набор обучающих заданий, который должен соответствовать следующим критериям:
    <ul>
     <li>
      <u>
       Полнота
      </u>
      – покрытие всех случаев из инструкции, при условии наличия соответствующих
                    примеров.
     </li>
     <li>
      <u>
       Содержательность
      </u>
      – примерно одинаковое количество информации для каждого случая. Чем
                    сложнее случай, тем больше обучающих примеров может потребоваться для необходимого количества
                    информации.
     </li>
    </ul>
   </li>
  </ul>
  <p>
   Для каждого задания вам требуется:
  </p>
  <ul>
   <li>
    Решить задание, либо правильно – как это сделал бы исполнитель согласно инструкции, либо специально неправильно –
допустите ошибку, нарушив один из важных пунктов инструкции.
   </li>
   <li>
    В поле
    <code>
     EVAL
    </code>
    соответственно выберите, правильно выполнили задание или нет.
   </li>
   <li>
    Если задание
    <strong>
     некорректное
    </strong>
    – соответствующий случай не описан в инструкции, оно вообще
            не соответствует инструкции, возникли технические сложности вроде ошибки 404, либо по какой-то иной
            причине, выберите
    <code>
     Нет
    </code>
    в поле
    <code>
     OK
    </code>
    и укажите
    <code>
     COMMENT
    </code>
    с описанием
            проблемы.
   </li>
   <li>
    Если вышеперечисленных проблем нет, то задание
    <strong>
     корректное
    </strong>
    , выберите
    <code>
     Да
    </code>
    в поле
    <code>
     OK
    </code>
    . Если вы допустили при выполнении задания специальную ошибку или считаете, что задание должно попасть в обучение, укажите
    <code>
     COMMENT
    </code>
    ,
            исполнители с ним смогут ознакомиться при прохождении обучения. В противном случае, оставьте
    <code>
     COMMENT
    </code>
    пустым.
   </li>
  </ul>
  <h2>
   Проверка решенных заданий заказчика
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
   проверка (разметка решений)
   </em>
   в названии и примечанием
   <em>
    Проверка заданий
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-33" type="checkbox"/>
   <label for="hd-33">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Сценарий эквивалентен предыдущему, с тем лишь отличием, что заказчик предоставляет задания с решениями. В поле
   <code>
    EVAL
   </code>
   выберите, верно выполнено задание или нет.
  </p>
  <p>
   Правила разметки
   <em>
    объектов
   </em>
   (решений) немного изменятся. Решение
   <em>
    некорректное
   </em>
   , если:
  </p>
  <ul>
   <li>
    Некорректно задание (см. выше критерии и соответствующие действия)
   </li>
   <li>
    Некорректно решение – оно не соответствует инструкции, выберите
    <code>
     Нет
    </code>
    в поле
    <code>
     OK
    </code>
    и укажите
            причину в
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <h2>
   Проверка качества разметки
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка решений)
   </em>
   в названии и примечанием
   <em>
    Проверка качества разметки
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-34" type="checkbox"/>
   <label for="hd-34">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="verification-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="verification-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Сценарий эквивалентен предыдущему. Источник решений в данном сценарии – разметка исполнителей. Оценивать нужно только правильность решения.
  </p>
  <p>
   Решение
   <em>
    некорректное
   </em>
   , если оно не соответствует инструкции, выберите
   <code>
    Нет
   </code>
   в поле
   <code>
    OK
   </code>
   и опционально укажите причину в
   <code>
    COMMENT
   </code>
   .
  </p>
 </div>
</div>"""  # noqa

annotation_expert_solution_instruction_en = """<h1>
 Instructions for workers
</h1>
<div>
 <div>
  <p>
   You will see solutions to tasks completed by the instruction below. Evaluate solutions according to this instruction.
  </p>
 </div>
 <h1>
  Instructions according to which solutions were given
 </h1>
 <div>
  Transcribe the audio
 </div>
</div>
<div>
 <input class="hide" id="hd-101" type="checkbox"/>
 <label for="hd-101">
  <strong>
   Expert labeling
  </strong>
 </label>
 <div>
  <h1>
   Task purpose
  </h1>
  <p>
   Your goal is to be an intermediary between the customer and the workers, providing bilateral guarantees:
  </p>
  <ul>
   <li>
    For performers, it is a guarantee of providing a clearly defined task.
   </li>
   <li>
    For the customer – a guarantee of providing quality solutions.
   </li>
  </ul>
  <p>
   <strong>
    Object
   </strong>
   – the task or the task with the solution (next, just a
   <em>
    solution
   </em>
   ) you are checking.
  </p>
  <p>
   <strong>
    Object source
   </strong>
   – customer or worker.
  </p>
  <p>
   The objects, their sources, as well as the necessary actions are determined by the
   <strong>
    scenario
   </strong>
   specified in the card of the task you are performing.
  </p>
  <h1>
   Objects labeling
  </h1>
  <p>
   The interface of the tasks offered to you is always built in the same way: the interface follows first of the
   <em>
    object
   </em>
   , then the fixed part with its expert labeling, separated by a horizontal line.
  </p>
  <p>
   The interface of the
   <em>
    object
   </em>
   depends on the task being solved by the customer. For example, if he
        solves a problem
   <em>
    transcript of speech from audio
   </em>
   , then the entire interface may look like this:
  </p>
  <div>
   <input class="hide" id="hd-30" type="checkbox"/>
   <label for="hd-30">
    <strong>
     Task
     <em>
      object
     </em>
     example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object"
src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_browser.png"
style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object"
src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_app.png"
style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <div>
   <input class="hide" id="hd-31" type="checkbox"/>
   <label for="hd-31">
    <strong>
     Solution
     <em>
      object
     </em>
     example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object"
src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_browser.png"
style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object"
src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_app.png"
style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   <em>
    Object
   </em>
   labeling includes 3 items:
  </p>
  <ul>
   <li>
    Binary evaluation of solution
    <code>
     EVAL
    </code>
    :
    <code>
     Yes
    </code>
    /
    <code>
     No
    </code>
    . This option should always
reflect whether the annotation was done accurately according to the instruction or not.
   </li>
   <li>
    Binary evaluation
    <code>
     OK
    </code>
    :
    <em>
     Yes
    </em>
    /
    <em>
     No
    </em>
    .
   </li>
   <li>
    Textual comment
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <p>
   The way to fill in these items depends on the
   <em>
    scenario
   </em>
   .
  </p>
  <h1>
   Scenarios
  </h1>
  <h2>
   Checking the customer's tasks
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (task labeling)
   </em>
   in the title and the note
   <em>
    Task verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-32" type="checkbox"/>
   <label for="hd-32">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Not all customers understand well how best to compile instructions and the interface of tasks so that workers
        clearly understand the task and had no difficulties in performing it.
  </p>
  <p>
   Let's list the criteria for a well-formulated task:
  </p>
  <ul>
   <li>
    <u>
     Completeness
    </u>
    - the instructions list all the cases observed in the data stream.
   </li>
   <li>
    <u>
     Clarity
    </u>
    - the instruction is written in a simple and understandable language.
   </li>
   <li>
    <u>
     Consistency
    </u>
    – there are no points in the instructions that contradict each other.
   </li>
   <li>
    <u>
     Brevity
    </u>
    - the instruction contains a minimum of information necessary to explain the essence of the
            task.
   </li>
   <li>
    <u>
     Convenience
    </u>
    - the task interface is convenient and involves a minimum of actions to perform the
            task.
   </li>
  </ul>
  <p>
   You will be shown the customer's tasks. The purpose of this scenario:
  </p>
  <ul>
   <li>
    Give feedback to the customer, if necessary, to rework the tasks. Types of feedback are:
    <ul>
     <li>
      <u>
       By-
       <em>
        object
       </em>
      </u>
      , which you specify when labeling the object.
     </li>
     <li>
      <u>
       General
      </u>
      , which you can inform in a chat with the customer.
     </li>
    </ul>
   </li>
   <li>
    Create a set of training tasks that must meet the following criteria:
    <ul>
     <li>
      <u>
       Completeness
      </u>
      - coverage of all cases from the instructions, subject to the availability of
                    appropriate examples.
     </li>
     <li>
      <u>
       Informativeness
      </u>
      – approximately the same amount of information for each case. The more
                    complicated the case, the more training examples may be required for the required amount of
                    information.
     </li>
    </ul>
   </li>
  </ul>
  <p>
   For each task you need:
  </p>
  <ul>
   <li>
    Complete the task either accurately – as the worker would do according to the instructions, or make some errors on
purpose, violating one of the important points of the instructions.
   </li>
   <li>
    In
    <code>
     EVAL
    </code>
    field choose whether you completed the task accurately or not.
   </li>
   <li>
    Perform the task as the worker would do according to the instructions.
   </li>
   <li>
    If the task is
    <strong>
     incorrect
    </strong>
    - the corresponding case is not described in the instructions, it
            is generally does not comply with the instructions, there were technical difficulties like error 404, or
            for some other reason, choose
    <code>
     No
    </code>
    in
    <code>
     OK
    </code>
    field and specify
    <code>
     COMMENT
    </code>
    with a problems description.
   </li>
   <li>
    If there are no problems listed above, then the task is
    <strong>
     correct
    </strong>
    , choose
    <code>
     Yes
    </code>
    in
    <code>
     OK
    </code>
    field. If you made some errors on purpose while completing the task or think that the task should be
            included in the training, specify
    <code>
     COMMENT
    </code>
    , which workers will be able to learn during
            training. Otherwise, leave
    <code>
     COMMENT
    </code>
    empty.
   </li>
  </ul>
  <h2>
   Checking the customer's solved tasks
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    check (solution labeling)
   </em>
   in the title and the note
   <em>
    Task verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-33" type="checkbox"/>
   <label for="hd-33">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser"
src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_browser.png"
style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app"
src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_app.png"
style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   The scenario is equivalent to the previous one, with the only difference that the customer provides tasks with
        solutions. In
   <code>
    EVAL
   </code>
   field choose, whether you've completed the task accurately or not.
  </p>
  <p>
   The rules for labeling of
   <em>
    objects
   </em>
   (solutions) will change slightly. The solution is
   <em>
    incorrect
   </em>
   if:
  </p>
  <ul>
   <li>
    The task is incorrect (see the criteria and corresponding actions above)
   </li>
   <li>
    The solution is incorrect – it does not comply with the instructions, choose
    <code>
     No
    </code>
    in
    <code>
     OK
    </code>
    field and specify the reason in
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <h2>
   Labeling quality verification
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (solution labeling)
   </em>
   in the title and the note
   <em>
    Labeling quality verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-34" type="checkbox"/>
   <label for="hd-34">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   The scenario is equivalent to the previous one. In this scenario tasks were solved by workers. You should only evaluate the correctness of the
   <strong>
    solution
   </strong>
  </p>
  <p>
   The solution is
   <em>
    incorrect
   </em>
   if it does not comply with the instructions, choose
   <code>
    No
   </code>
   in
   <code>
    OK
   </code>
   field and specify the reason in
   <code>
    COMMENT
   </code>
   .
  </p>
 </div>
</div>"""  # noqa

annotation_expert_verification_instruction_ru = """<h1>
 Инструкция для исполнителей
</h1>
<div>
 Запишите звучащие на аудио слова
</div>
<div>
 <input class="hide" id="hd-101" type="checkbox"/>
 <label for="hd-101">
  <strong>
   Экспертная разметка
  </strong>
 </label>
 <div>
  <h1>
   Цель задания
  </h1>
  <p>
   Ваша цель – быть посредником между заказчиком и исполнителями, предоставляя двусторонние гарантии:
  </p>
  <ul>
   <li>
    Для исполнителей – гарантия предоставления четко поставленной задачи.
   </li>
   <li>
    Для заказчика – гарантия предоставления качественных решений.
   </li>
  </ul>
  <p>
   <strong>
    Объект
   </strong>
   – проверяемое вами задание или задание с решением (далее просто
   <em>
    решение
   </em>
   ).
  </p>
  <p>
   <strong>
    Источник объекта
   </strong>
   – заказчик или исполнитель.
  </p>
  <p>
   Объекты, их источники, а также необходимые действия, определяются
   <strong>
    сценарием
   </strong>
   , указанным в
        карточке выполняемого вами задания.
  </p>
  <h1>
   Разметка объектов
  </h1>
  <p>
   Интерфейс предлагаемых вам заданий всегда построен одинаковым образом: сначала следует интерфейс
   <em>
    объекта
   </em>
   , затем фиксированная часть с его экспертной разметкой, отделяемая горизонтальной чертой.
  </p>
  <p>
   Интерфейс
   <em>
    объекта
   </em>
   зависит от решаемой заказчиком задачи. Например, если он решает задачу
   <em>
    расшифровка речи из аудиозаписей
   </em>
   , то интерфейс целиком может выглядеть так:
  </p>
  <div>
   <input class="hide" id="hd-30" type="checkbox"/>
   <label for="hd-30">
    <strong>
     Пример
     <em>
      объекта
     </em>
     -задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <div>
   <input class="hide" id="hd-31" type="checkbox"/>
   <label for="hd-31">
    <strong>
     Пример
     <em>
      объекта
     </em>
     -решения
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Разметка
   <em>
    объекта
   </em>
   включает в себя 2 пункта:
  </p>
  <ul>
   <li>
    Бинарная оценка
    <code>
     OK
    </code>
    :
    <em>
     Да
    </em>
    /
    <em>
     Нет
    </em>
    .
   </li>
   <li>
    Текстовый комментарий
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <p>
   Способ заполнения пунктов
   <code>
    OK
   </code>
   и
   <code>
    COMMENT
   </code>
   зависит от
   <em>
    сценария
   </em>
   .
  </p>
  <h1>
   Сценарии
  </h1>
  <h2>
   Проверка заданий заказчика
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка заданий)
   </em>
   в названии и примечанием
   <em>
    Проверка заданий
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-32" type="checkbox"/>
   <label for="hd-32">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Не все заказчики хорошо понимают, как лучше составлять инструкцию и интерфейс заданий так, чтобы исполнители
        четко понимали поставленное задание и не испытывали трудностей при решении.
  </p>
  <p>
   Даже при наличии хорошо составленной инструкции, размечаемые данные могут не соответствовать написанному в
        инструкции.
  </p>
  <p>
   Перечислим критерии хорошо сформулированного задания:
  </p>
  <ul>
   <li>
    <u>
     Полнота
    </u>
    – в инструкции перечислены все случаи, наблюдаемые в потоке размечаемых данных.
   </li>
   <li>
    <u>
     Понятность
    </u>
    – инструкция написана простым и понятным языком.
   </li>
   <li>
    <u>
     Непротиворечивость
    </u>
    – в инструкции нет пунктов, которые противоречат друг другу.
   </li>
   <li>
    <u>
     Краткость
    </u>
    – инструкция содержит минимум информации, нужный для объяснения сути задания.
   </li>
   <li>
    <u>
     Удобство
    </u>
    – интерфейс заданий удобен и предполагает минимум действий для решения задания.
   </li>
  </ul>
  <p>
   Вам будут показаны задания заказчика. Цель данного сценария:
  </p>
  <ul>
   <li>
    Дать обратную связь заказчику при необходимости доработать задания. Обратная связь бывает:
    <ul>
     <li>
      <u>
       По-
       <em>
        объектная
       </em>
      </u>
      , которую вы укажете при разметке объекта.
     </li>
     <li>
      <u>
       Общая
      </u>
      , которую вы можете сообщить в чате с заказчиком.
     </li>
    </ul>
   </li>
   <li>
    Сформировать набор обучающих заданий, который должен соответствовать следующим критериям:
    <ul>
     <li>
      <u>
       Полнота
      </u>
      – покрытие всех случаев из инструкции, при условии наличия соответствующих
                    примеров.
     </li>
     <li>
      <u>
       Содержательность
      </u>
      – примерно одинаковое количество информации для каждого случая. Чем
                    сложнее случай, тем больше обучающих примеров может потребоваться для необходимого количества
                    информации.
     </li>
    </ul>
   </li>
  </ul>
  <p>
   Для каждого задания вам требуется:
  </p>
  <ul>
   <li>
    Решить задание, либо правильно – как это сделал бы исполнитель согласно инструкции, либо специально неправильно –
допустите ошибку, нарушив один из важных пунктов инструкции.
   </li>
   <li>
    В поле
    <code>
     EVAL
    </code>
    соответственно выберите, правильно выполнили задание или нет.
   </li>
   <li>
    Если задание
    <strong>
     некорректное
    </strong>
    – соответствующий случай не описан в инструкции, оно вообще
            не соответствует инструкции, возникли технические сложности вроде ошибки 404, либо по какой-то иной
            причине, выберите
    <code>
     Нет
    </code>
    в поле
    <code>
     OK
    </code>
    и укажите
    <code>
     COMMENT
    </code>
    с описанием
            проблемы.
   </li>
   <li>
    Если вышеперечисленных проблем нет, то задание
    <strong>
     корректное
    </strong>
    , выберите
    <code>
     Да
    </code>
    в поле
    <code>
     OK
    </code>
    . Если вы допустили при выполнении задания специальную ошибку или считаете, что задание должно попасть в обучение, укажите
    <code>
     COMMENT
    </code>
    ,
            исполнители с ним смогут ознакомиться при прохождении обучения. В противном случае, оставьте
    <code>
     COMMENT
    </code>
    пустым.
   </li>
  </ul>
  <h2>
   Проверка решенных заданий заказчика
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    проверка (разметка решений)
   </em>
   в названии и примечанием
   <em>
    Проверка заданий
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-33" type="checkbox"/>
   <label for="hd-33">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Сценарий эквивалентен предыдущему, с тем лишь отличием, что заказчик предоставляет задания с решениями.
  </p>
  <p>
   Правила разметки
   <em>
    объектов
   </em>
   (решений) немного изменятся. Решение
   <em>
    некорректное
   </em>
   , если:
  </p>
  <ul>
   <li>
    Некорректно задание (см. выше критерии и соответствующие действия)
   </li>
   <li>
    Некорректно решение – оно не соответствует инструкции, выберите
    <code>
     Нет
    </code>
    в поле
    <code>
     OK
    </code>
    и укажите
            причину в
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <h2>
   Проверка качества разметки
  </h2>
  <p>
   В ленте заданий Толоки вы увидите карточку с суффиксом
   <em>
    (разметка решений)
   </em>
   в названии и примечанием
   <em>
    Проверка качества разметки
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-34" type="checkbox"/>
   <label for="hd-34">
    <strong>
     Пример карточки задания
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="verification-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="verification-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Сценарий эквивалентен предыдущему. Источник решений в данном сценарии – разметка исполнителей. Оценивать нужно только правильность решения.
  </p>
  <p>
   Решение
   <em>
    некорректное
   </em>
   , если оно не соответствует инструкции, выберите
   <code>
    Нет
   </code>
   в поле
   <code>
    OK
   </code>
   и опционально укажите причину в
   <code>
    COMMENT
   </code>
   .
  </p>
 </div>
</div>"""  # noqa

annotation_expert_verification_instruction_en = """<h1>
 Instructions for workers
</h1>
<div>
 Transcribe the audio
</div>
<div>
 <input class="hide" id="hd-101" type="checkbox"/>
 <label for="hd-101">
  <strong>
   Expert labeling
  </strong>
 </label>
 <div>
  <h1>
   Task purpose
  </h1>
  <p>
   Your goal is to be an intermediary between the customer and the workers, providing bilateral guarantees:
  </p>
  <ul>
   <li>
    For performers, it is a guarantee of providing a clearly defined task.
   </li>
   <li>
    For the customer – a guarantee of providing quality solutions.
   </li>
  </ul>
  <p>
   <strong>
    Object
   </strong>
   – the task or the task with the solution (next, just a
   <em>
    solution
   </em>
   ) you are checking.
  </p>
  <p>
   <strong>
    Object source
   </strong>
   – customer or worker.
  </p>
  <p>
   The objects, their sources, as well as the necessary actions are determined by the
   <strong>
    scenario
   </strong>
   specified in the card of the task you are performing.
  </p>
  <h1>
   Objects labeling
  </h1>
  <p>
   The interface of the tasks offered to you is always built in the same way: the interface follows first of the
   <em>
    object
   </em>
   , then the fixed part with its expert labeling, separated by a horizontal line.
  </p>
  <p>
   The interface of the
   <em>
    object
   </em>
   depends on the task being solved by the customer. For example, if he
        solves a problem
   <em>
    transcript of speech from audio
   </em>
   , then the entire interface may look like this:
  </p>
  <div>
   <input class="hide" id="hd-30" type="checkbox"/>
   <label for="hd-30">
    <strong>
     Task
     <em>
      object
     </em>
     example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <div>
   <input class="hide" id="hd-31" type="checkbox"/>
   <label for="hd-31">
    <strong>
     Solution
     <em>
      object
     </em>
     example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-object" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-ui_expert-labeling-of-solutions_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   <em>
    Object
   </em>
   labeling includes 2 items:
  </p>
  <ul>
   <li>
    Binary evaluation
    <code>
     OK
    </code>
    :
    <em>
     Yes
    </em>
    /
    <em>
     No
    </em>
    .
   </li>
   <li>
    Textual comment
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <p>
   The way to fill in these items depends on the
   <em>
    scenario
   </em>
   .
  </p>
  <h1>
   Scenarios
  </h1>
  <h2>
   Checking the customer's tasks
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (task labeling)
   </em>
   in the title and the note
   <em>
    Task verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-32" type="checkbox"/>
   <label for="hd-32">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-tasks_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   Not all customers understand well how best to compile instructions and the interface of tasks so that workers
        clearly understand the task and had no difficulties in performing it.
  </p>
  <p>
   Let's list the criteria for a well-formulated task:
  </p>
  <ul>
   <li>
    <u>
     Completeness
    </u>
    - the instructions list all the cases observed in the data stream.
   </li>
   <li>
    <u>
     Clarity
    </u>
    - the instruction is written in a simple and understandable language.
   </li>
   <li>
    <u>
     Consistency
    </u>
    – there are no points in the instructions that contradict each other.
   </li>
   <li>
    <u>
     Brevity
    </u>
    - the instruction contains a minimum of information necessary to explain the essence of the
            task.
   </li>
   <li>
    <u>
     Convenience
    </u>
    - the task interface is convenient and involves a minimum of actions to perform the
            task.
   </li>
  </ul>
  <p>
   You will be shown the customer's tasks. The purpose of this scenario:
  </p>
  <ul>
   <li>
    Give feedback to the customer, if necessary, to rework the tasks. Types of feedback are:
    <ul>
     <li>
      <u>
       By-
       <em>
        object
       </em>
      </u>
      , which you specify when labeling the object.
     </li>
     <li>
      <u>
       General
      </u>
      , which you can inform in a chat with the customer.
     </li>
    </ul>
   </li>
   <li>
    Create a set of training tasks that must meet the following criteria:
    <ul>
     <li>
      <u>
       Completeness
      </u>
      - coverage of all cases from the instructions, subject to the availability of
                    appropriate examples.
     </li>
     <li>
      <u>
       Informativeness
      </u>
      – approximately the same amount of information for each case. The more
                    complicated the case, the more training examples may be required for the required amount of
                    information.
     </li>
    </ul>
   </li>
  </ul>
  <p>
   For each task you need:
  </p>
  <ul>
   <li>
    Complete the task either accurately – as the worker would do according to the instructions, or make some errors on
purpose, violating one of the important points of the instructions.
   </li>
   <li>
    In
    <code>
     EVAL
    </code>
    field choose whether you completed the task accurately or not.
   </li>
   <li>
    Perform the task as the worker would do according to the instructions.
   </li>
   <li>
    If the task is
    <strong>
     incorrect
    </strong>
    - the corresponding case is not described in the instructions, it
            is generally does not comply with the instructions, there were technical difficulties like error 404, or
            for some other reason, choose
    <code>
     No
    </code>
    in
    <code>
     OK
    </code>
    field and specify
    <code>
     COMMENT
    </code>
    with a problems description.
   </li>
   <li>
    If there are no problems listed above, then the task is
    <strong>
     correct
    </strong>
    , choose
    <code>
     Yes
    </code>
    in
    <code>
     OK
    </code>
    field. If you made some errors on purpose while completing the task or think that the task should be
            included in the training, specify
    <code>
     COMMENT
    </code>
    , which workers will be able to learn during
            training. Otherwise, leave
    <code>
     COMMENT
    </code>
    empty.
   </li>
  </ul>
  <h2>
   Checking the customer's solved tasks
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    check (solution labeling)
   </em>
   in the title and the note
   <em>
    Task verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-33" type="checkbox"/>
   <label for="hd-33">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_test-launch-on-solutions_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   The scenario is equivalent to the previous one, with the only difference that the customer provides tasks with
        solutions.
  </p>
  <p>
   The rules for labeling of
   <em>
    objects
   </em>
   (solutions) will change slightly. The solution is
   <em>
    incorrect
   </em>
   if:
  </p>
  <ul>
   <li>
    The task is incorrect (see the criteria and corresponding actions above)
   </li>
   <li>
    The solution is incorrect – it does not comply with the instructions, choose
    <code>
     No
    </code>
    in
    <code>
     OK
    </code>
    field and specify the reason in
    <code>
     COMMENT
    </code>
    .
   </li>
  </ul>
  <h2>
   Labeling quality verification
  </h2>
  <p>
   In the Toloka task feed, you will see a card with the suffix
   <em>
    (solution labeling)
   </em>
   in the title and the note
   <em>
    Labeling quality verification
   </em>
   :
  </p>
  <div>
   <input class="hide" id="hd-34" type="checkbox"/>
   <label for="hd-34">
    <strong>
     Task card example
    </strong>
   </label>
   <div>
    <table>
     <tbody>
      <tr>
       <td style="text-align:center">
        <h2>
         Browser
        </h2>
       </td>
       <td style="text-align:center">
        <h2>
         Mobile app
        </h2>
       </td>
      </tr>
      <tr>
       <td>
        <img alt="task-card-browser" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_browser.png" style="width:100%;max-width:500px"/>
       </td>
       <td>
        <img alt="task-card-app" src="https://storage.yandexcloud.net/crowdom-public/instructions/experts/en/task-card_verification_annotation_app.png" style="width:100%;max-width:500px"/>
       </td>
      </tr>
     </tbody>
    </table>
   </div>
  </div>
  <p>
   The scenario is equivalent to the previous one. In this scenario tasks were solved by workers. You should only evaluate the correctness of the
   <strong>
    solution
   </strong>
  </p>
  <p>
   The solution is
   <em>
    incorrect
   </em>
   if it does not comply with the instructions, choose
   <code>
    No
   </code>
   in
   <code>
    OK
   </code>
   field and specify the reason in
   <code>
    COMMENT
   </code>
   .
  </p>
 </div>
</div>"""  # noqa


def test_classification_default_ru():
    assert client.get_instruction(classification_task_spec_p_ru) == client.prettify_html(
        instruction.css + classification_default_instruction_ru + instruction.acceptance['RU']
    )


def test_classification_default_en():
    assert client.get_instruction(classification_task_spec_p_en) == client.prettify_html(
        instruction.css + classification_default_instruction_en + instruction.acceptance['EN']
    )


def test_classification_expert_task_ru():
    assert client.get_instruction(classification_task_expert_task_spec_p_ru) == client.prettify_html(
        instruction.css + classification_expert_task_instruction_ru
    )


def test_classification_expert_task_en():
    assert client.get_instruction(classification_task_expert_task_spec_p_en) == client.prettify_html(
        instruction.css + classification_expert_task_instruction_en
    )


def test_classification_expert_solution_ru():
    assert client.get_instruction(classification_solution_expert_task_spec_p_ru) == client.prettify_html(
        instruction.css + classification_expert_solution_instruction_ru
    )


def test_classification_expert_solution_en():
    assert client.get_instruction(classification_solution_expert_task_spec_p_en) == client.prettify_html(
        instruction.css + classification_expert_solution_instruction_en
    )


def test_annotation_default_ru():
    assert client.get_instruction(annotation_task_spec_p_ru) == client.prettify_html(
        instruction.css + annotation_default_instruction_ru + instruction.acceptance['RU']
    )


def test_annotation_default_en():
    assert client.get_instruction(annotation_task_spec_p_en) == client.prettify_html(
        instruction.css + annotation_default_instruction_en + instruction.acceptance['EN']
    )


def test_annotation_expert_task_ru():
    assert client.get_instruction(annotation_task_expert_task_spec_p_ru) == client.prettify_html(
        instruction.css + annotation_expert_task_instruction_ru
    )


def test_annotation_expert_task_en():
    assert client.get_instruction(annotation_task_expert_task_spec_p_en) == client.prettify_html(
        instruction.css + annotation_expert_task_instruction_en
    )


def test_annotation_expert_solution_ru():
    assert client.get_instruction(annotation_task_expert_task_spec_p_ru.check) == client.prettify_html(
        instruction.css + annotation_expert_solution_instruction_ru
    )


def test_annotation_expert_solution_en():
    assert client.get_instruction(annotation_task_expert_task_spec_p_en.check) == client.prettify_html(
        instruction.css + annotation_expert_solution_instruction_en
    )


def test_annotation_expert_verification_ru():
    assert client.get_instruction(annotation_solution_expert_task_spec_p_ru) == client.prettify_html(
        instruction.css + annotation_expert_verification_instruction_ru
    )


def test_annotation_expert_verification_en():
    assert client.get_instruction(annotation_solution_expert_task_spec_p_en) == client.prettify_html(
        instruction.css + annotation_expert_verification_instruction_en
    )
