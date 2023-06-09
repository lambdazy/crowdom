# Руководство пользователя DataForge

DataForge – сервис, упрощающий работу с разметкой данных.

DataForge позволяет описывать и запускать ваши задачи по разметке, используя простой Python 3 код, не требуя знаний
специфики конкретных краудсорсинговых платформ, самостоятельной работы по обеспечению качества разметки, прямой
коммуникации с исполнителями. В качестве платформы DataForge использует [Толоку](https://toloka.ai).

DataForge позволяет решать такие задачи, как классификация текстов, расшифровка аудиозаписей, выделение объектов на
изображениях, проведение side-by-side экспериментов и т.д. Подробнее о видах решаемых задач читайте в
разделе [Общих понятий](#concepts).

Использовать DataForge рекомендуется в среде Jupyter Lab, удобнее всего это делать
в [DataSphere](https://cloud.yandex.ru/services/datasphere).

## Рекомендации по изучению руководства

Если раньше вы уже работали с разметкой данных, попробуйте начать с раздела [Быстрый старт](#quick-start), иначе мы
рекомендуем вам сперва ознакомиться с [Общими понятиями](#concepts). В [примерах](../examples) приведены ссылки на
соответствующие разделы руководства.

# Содержание

- [Быстрый старт](#quick-start)
- [Общие понятия](#concepts)
    - [Терминология](#terms)
    - [Качество разметки](#quality)
- [Пошаговые инструкции](#instructions)
    - [Описание задания](#task-def)
    - [Пробный запуск](#test-launch)
    - [Параметры разметки](#config)
- [Помощь](#support)

# Быстрый старт <a name="quick-start"></a>

Создайте аккаунт заказчика в [Толоке](https://toloka.ai).

<details>

<summary><u>Рекомендации по созданию аккаунта</u></summary>

Для регистрации заказчика рекомендуется завести отдельный Яндекс аккаунт, а не использовать свой личный. Позже вы
сможете выдать доступ для своего личного аккаунта, чтобы не приходилось переключаться между аккаунтами. Используя личный
аккаунт для заказчика Толоки, вы не сможете сами просматривать свои задания как исполнитель, что удобно в ряде случаев.
</details>

Установите DataForge:

```bash
pip install crowdom
```

Изучите [примеры](../examples) решения разных задач и попробуйте решить свою.

# Общие понятия <a name="concepts"></a>

В данном разделе вы ознакомитесь с основными понятиями и используемой терминологией, необходимыми для понимания
последующих инструкций.

## Терминология <a name="terms"></a>

**Задача** – ваш сценарий разметки данных. Примеры задач: классификация текстов, расшифровка аудиозаписей, кластеризация
новостных статей и т.д.

**Объект** – элемент входных или выходных данных вашей задачи.

В данный момент поддерживаются следующие объекты:

- <details><summary><u>Текст</u></summary>
  Последовательность Unicode символов. Как правило, представляет собой текст на естественном языке.</details>
- <details><summary><u>Изображение</u></summary>
  Фотография либо иное изображение, которое по ссылке может отобразиться в браузере.</details>
- <details><summary><u>Аудио</u></summary>
  Аудиозапись, которая по ссылке может воспроизвестись в браузере.</details>
- <details><summary><u>Видео</u></summary>
  Видеозапись, которая по ссылке может воспроизвестись в браузере.</details>
- <details><summary><u>Класс</u></summary>
  Стандартный или определяемый пользователем набор вариантов, между которыми исполнители будут делать выбор.</details>

В будущем планируется возможность самому объявлять свой объект.

**Функция** – принимает набор объектов на вход (**задание**) и отдает набор объектов на выход (**решение**).

Функция соответствует вашей задаче разметки и определяет то, в каком виде вашу задачу будут решать исполнители. Мы
говорим, что функция _решает_ вашу _задачу_ разметки.

Примеры функций:

- `TextClassification(Text) = UserClass`
- `ImageSideBySide(Image1, Image2) = Choice`
- `ImageSegmentation(Image) = Area`
- `AudioTransript(Audio) = Text`
- `SpeechRecording(Text) = Audio`

Аргументы функции – это входные данные (задание), которые исполнитель изучит в интерфейсе задания. Результатом работы
исполнителя станут выходные данные (решение). Например, в задаче расшифровок аудиозаписей, исполнитель прослушает
аудиозапись (входные данные) и запишет текст звучащей на ней речи (выходные данные).

Есть два типа решений:

- Решения **ограниченной** размерности, когда исполнителю предлагается сделать выбор из ограниченного набора вариантов.
- Решения **неограниченной** размерности, когда пространство возможных решений не ограничено заранее.

Решения неограниченной размерности – это записанный текст, аудиозапись, выделение объектов на изображениях и т.п.
Вследствие неоднозначностей в естественных языках или помехах на аудиозаписях, расшифровку аудиозаписи можно написать
разными способами. Также можно по-разному выделить объект на изображении, т.к. при смещении в сторону на несколько
пикселей задача все еще решается, либо изображение может быть плохого качества и непонятно, где проходят границы
объектов.

Качество для данных типов решений обеспечивается разными способами, подробнее про это написано в
разделе [Качество разметки](#quality).

<details>

<summary><u>О разнице между ограниченной и неограниченной размерностью</u></summary>

Порой бывает сложно определить, с каким типом решения мы имеем дело. Например, задачу выделения объектов на изображениях
в каком-то смысле можно считать задачей с решением ограниченной размерности, так как изображение имеет конечные ширину и
высоту в пикселях и число вариантов, тем самым, ограничено.

Определить тип решения можно, представив, среди какого числа вариантов исполнители будут выбирать в типичном случае,
когда решают вашу задачу. Если число вариантов исчисляется единицами или десятками, то это можно считать решением
ограниченной размерности.
</details>

Имея эти два типа решений, мы вводим два основных типа функций:

- Функции **классификации** (решения ограниченной размерности)
- Функции **аннотации** (решения неограниченной размерности)

Функции классификации решают такие задачи, как классификация объектов, их сравнение, оценка решений.

Функции аннотации решают такие задачи, как расшифровка аудиозаписей, выделение объектов на картинках, разметка кадров
видеозаписей и т.д.

<details>
<summary><u>О других видах задач</u></summary>

Есть также другие виды задач, которые мы не упомянули.

Например, с помощью попарного сравнения объектов можно решить задачи _ранжирования_ и _кластеризации_. В данной версии
DataForge это еще не реализовано.

Существуют задачи _генерации контента_ по некоторой инструкции. Здесь все зависит от конкретной задачи, в каких-то
случаях генерацию можно рассмотреть как задачу аннотации с "пустым входом".

Также с помощью краудсорсинга можно проводить опросы.

</details>

## Качество разметки <a name="quality"></a>

На то, насколько качественно будет решена ваша задача, оказывают влияние следующие факторы:

- Качество работы исполнителей.
- Количество мнений о решении задания.

Качество итогового решения задания определяется **уверенностью** (_confidence_) – _вероятностью_ того, что это решение
правильно, числом от 0 (решение неверное) до 1 (решение верное).

### Контроль качества решений <a name="solution-quality"></a>

В краудсорсинговых платформах не все исполнители хорошо справляются с задачами, для получения качественной разметки
нужно контролировать их работу и мотивировать выполнять задания добросовестно.

Контроль качества решений зависит от типа функции:

- Для _функций классификации_ мы можем знать точное решение задания. Исполнителям передаются как обычные задания (_real
  tasks_), так и задания, решения которых мы уже знаем – **контрольные задания** (_control tasks_). Контроль
  осуществляется путем анализа решений контрольных заданий.
- Для _функций аннотации_, решения заданий проверяются другими исполнителями. Проверка решений, в свою очередь, является
  функцией классификации, т.к. исполнителей обычно просят оценить решение бинарно (правильно / неправильно), или по
  какой-то фиксированной школе (например, оценка от 1 до 5). Поэтому проверки решений можно контролировать также с
  помощью контрольных заданий.

<details>
<summary><u>О других способах контроля качества классификаций</u></summary>
Существует также подход, когда вместо сравнения с известными решениями контрольных заданий, решение исполнителя
сравнивается с решениями этого же задания других исполнителей (см. раздел <a href="#overlap">Сбор множества мнений</a>),
если решение исполнителя существенно отличается от решения большинства, то с высокой вероятностью его решение неверное.

В данный момент в DataForge этот подход не применяется, так как он не защищен от ситуации массового сговора исполнителей
(все договорились указывать один и тот же вариант).
</details>

<details>
<summary><u>О других способах контроля качества аннотаций</u></summary>
Существуют также другие способы по контролю качества аннотаций:
<ul>
    <li>Исполнители не оценивают решение, а самостоятельно вносят исправления или указывают ошибки. Такой способ в
данный момент не поддержан в DataForge.</li>
    <li>Можно составлять контрольные задания для функций аннотации и сравнивать решение с известными решением нестрого,
например, допуская отклонение на несколько пикселей при выделении объекта на картинке, либо обозначая допустимое
расстояние Левенштейна между текстом исполнителя и ожидаемым текстом. В DataForge такой подход не поддерживается,
поскольку он сложно обобщается и имеет ряд недостатков на практике.</li>
    <li>Можно собирать несколько аннотаций и генерировать итоговое решение с помощью специализированного алгоритма
агрегации. Такой подход в данный момент также не применяется ввиду сложностей в обобщении. Кроме того, качество
полученных решений все еще нужно контролировать.</li>
</ul>
</details>

### Сбор множества мнений <a name="overlap"></a>

Зачастую задачу сложно решить, располагая решением лишь одного исполнителя, и лучше собрать множество разных мнений,
выбрав решение мнением большинства или каким-то другим [механизмом агрегации](#quality-config).

Прием со сбором множества мнений о решении называется **перекрытием** (_overlap_). Для простых задач, решение которых
очевидно, достаточно небольшого числа мнений. Для сложных задач может потребоваться собрать большее число мнений, чтобы
достигнуть требуемого уровня уверенности в итоговом решении.

Например, вы решаете задачу определения животного на фотографии, и вы показали фотографию двум разным исполнителям
(_overlap_ = 2), один из которых сказал, что на фотографии кошка, другой – что собака. В итоге вы не уверены, какое
решение правильное. Если показать фотографию третьему исполнителю (_overlap_ = 3) и он согласится с мнением одного из
предыдущих, выбрав кошку или собаку, можно будет с большей степенью уверенности (_confidence_) выбрать его вариант.

В функциях аннотации, по оценкам других исполнителей мы можем решить, насколько мы уверены в полученном решении, и при
необходимости повторно дать задание другому исполнителю.

# Пошаговые инструкции <a name="instructions"></a>

Информация в этом разделе поможет вам лучше разобраться с кодом, приведенном в [примерах](../examples), и в итоге решить
с помощью DataForge собственную задачу.

## Описание задания <a name="task-def"></a>

В первую очередь нужно выбрать тип функции и ее аргументов согласно вашей задаче (см. раздел [Терминология](#terms)).

Затем нужно написать инструкцию для исполнителей, которую они изучат перед тем, как приступить к решению ваших задач.

Старайтесь делать инструкцию и задание в целом максимально короткими и понятными, это напрямую повлияет на качество
получаемых решений и привлекательность ваших заданий для исполнителей. Вы можете ознакомиться с рекомендациями Толоки по
поводу [декомпозиции заданий](https://toloka.ai/ru/knowledgebase/decomposition)
и [составлению инструкций](https://toloka.ai/ru/knowledgebase/instruction).

Вам также нужно указать примерное время выполнения одного задания (`task_duration_hint`), оно нужно
для [ценообразования](#pricing) и контроля качества решений. Определите это время, засекая время при
[самостоятельном решении](#test-launch) своих заданий.

<details>
<summary><u>Автоматический подсчет времени</u></summary>
В будущем в DataForge будет добавлена возможность автоматически определять время на выполнение задания, отталкиваясь от
типа объектов в задании и их объема (число символов в тексте, длительность аудиозаписи и т.д.), а также некоторой
метаинформации о том, какое внимание каждому из объектов нужно уделять при решении задания.
</details>

Старайтесь указать время выполнения задания с запасом, учитывая, что исполнители могут выполнять задания с мобильных
устройств, где взаимодействие с интерфейсом медленнее (например, набор текста), либо их Интернет может быть медленным,
из-за чего им дольше придется ждать загрузки медиаконтента в заданиях.

Заметим, что время выполнения задания желательно регулярно пересматривать, наблюдая по метрикам за тем, сколько в
реальности исполнители будут затрачивать на него времени. Это позволит делать цену и контроль качества более
адекватными.

## Пробный запуск <a name="test-launch"></a>

Перед тем, как публиковать задания в общий доступ для многих тысяч исполнителей, мы рекомендуем вам попробовать
выполнить его самим или с помощью [экспертов](experts-ru.md).

По собранной обратной связи вам может потребоваться уточнить инструкцию задания, либо его функцию, поменяв ее или
проведя [декомпозицию задания](https://toloka.ai/ru/knowledgebase/decomposition).

В итоге вы получите более понятное для исполнителей задание и сможете быстрее получить разметку высокого качества без
необходимости несколько раз уточнять задание "наживую", а также отвечать на множество однотипных вопросов исполнителей.

Из полученных во время пробного запуска решений также можно сформировать обучающие задания с подсказками, чтобы
исполнители перед решением ваших заданий смогли ознакомиться с основными примерами и случаями, возникающими на практике.

Подробнее о формировании группы экспертов, их функциях и взаимодействии с ними читайте в
соответствующем [разделе](experts-ru.md).

## Параметры разметки <a name="config"></a>

Настраивая параметры запуска разметки, вы определяете баланс между _качеством_, _стоимостью_ и _скоростью_.

Повысить качество можно, указав высокий минимальный порог _уверенности_ в правильном ответе. В случае функций
классификации для высокой уверенности может потребоваться большее [перекрытие](#overlap). В случае функций аннотации,
вам может потребоваться передать задачу большему числу исполнителей перед тем, как будет найдено решение с требуемой
уверенностью.

Данные меры приводят к большему числу решений, значит, к большей стоимости и длительности разметки.

Большей уверенности можно достичь, передавая задание более опытным исполнителям. Но, как правило, такие исполнители
ожидают большей оплаты и конкуренция за них выше, следовательно, стоимость снова возрастет, а скорость упадет.

Решения исполнителей можно _отклонять_ (_reject_), в таком случае оплата не будет производиться, а исполнитель будет в
праве подать апелляцию на пересмотр его работы. Отклонять решения можно на
основе [контроля их качества](#solution-quality), например, если доля правильно выполненных исполнителем заданий
(контрольных в случае функций классификации или обычных в случае функций аннотации) ниже заданного порога. Если решение
не отклоняется, то оно _принимается_ (_accept_).

Если задать слишком строгие настройки по контролю качества решений, то ваши задания могут стать менее привлекательными
для исполнителей, то есть упадет скорость, хоть стоимость и понизится. Кроме того, вам может потребоваться разбирать
большое количество апелляций (самостоятельно или с помощью [экспертов](experts-ru.md)).

В зависимости от решаемой вами задачи, какой-то из критериев (качество, стоимость, скорость) может оказаться более
важным, например, вам нужен максимальный объем размеченных данных в единицу времени и не так важно качество, либо,
наоборот, вам нужно достичь максимального качества, пожертвовав скоростью и стоимостью.

Пробуйте разные варианты настроек, следя за метриками разметки, чтобы подобрать оптимальный для вас вариант.

### Ценообразование <a name="pricing"></a>

Единица работы исполнителя, за которую он получает оплату – **страница заданий**. На странице заданий располагается
несколько заданий. Число заданий на странице определяется в основном объемом одного задания, если задание требует много
времени на выполнение, то оно может быть одно на странице, если задания небольшие, то их может быть несколько
(вплоть до 20-30).

В случае _функции классификации_, некоторые задания на странице будут контрольными, чтобы страницу заданий не отклонили,
доля правильно выполненных заданий должна быть не ниже заданной (`correct_control_task_ratio_for_acceptance`).
Абсолютное значение минимального числа правильно выполненных контрольных заданий считается как
`ceil(control_tasks_count * correct_control_task_ratio_for_acceptance)`, например, при 4 контрольных заданиях и
требуемой доле 0.7 получится `ceil(4 * 0.7) = 3`

Чем больше число контрольных заданий и требуемая доля правильно выполненных, тем меньше вероятность того, что
исполнитель случайно выберет правильные решения и его работа будет принята, хотя он выполнил ее недобросовестно.
Устойчивость к получению правильных решений в условиях случайного выбора называется **робастностью** (_robustness_).

<details>
<summary><u>Подробнее про случайный выбор</u></summary>
В некоторых задачах может иметь место априорное распределение вероятностей вариантов, т.е. какие-то варианты заведомо
более часто выбираются. В данный момент DataForge не учитывает это распределение при подсчете робастности.

Кроме того, подразумевается, что контрольные задания никак не отличаются от обычных (отсутствует bias в сторону
определенных вариантов и т.д.), т.е. их невозможно "вычислить" на странице заданий.
</details>

С другой стороны, большая доля контрольных заданий приводит к высокой переплате, ведь решения контрольных заданий не
несут никакой пользы, а служат только для обеспечения качества.

Долю контрольных заданий, следовательно, и переплату, можно уменьшить, сделав большое количество заданий на странице.
Рассмотрим пример. Предположим, что страницы заданий состоят из 10 заданий, из которых 3 задания – контрольные. Доля
контрольных заданий в этом случае – 30%, довольно много. Если расположить на странице 100 заданий, из которых будет 10
контрольных заданий, то их доля будет составлять уже 10%.

Но очень большие страницы заданий непривлекательны для исполнителей:

- Исполнитель может не располагать достаточным временем для их выполнения.
- Такие страницы тяжелее выполнять с точки зрения когнитивной нагрузки.
- Более ощутимый исполнителем риск не получить заработок (как из-за отклонения его работы, так и из-за проблем, не
  связанных напрямую с качеством его работы – потери Интернет-соединения, лагов в интерфейсе платформы и т.п.).

Наконец, ваши задания могут требовать задание определенного языка, а стоимость работы исполнителей зависит от места их
проживания.

Исходя из вышеперечисленных факторов, DataForge выбирает оптимальный вариант ценообразования для вашей задачи, определяя
стоимость страницы заданий, число заданий на ней и долю контрольных заданий. Выбор иллюстрируется графиками отношения
параметров робастности, доли контрольных заданий и предполагаемой длительности страницы заданий.

Вы также можете выбрать свой собственный вариант, пользуясь графиками в качестве подсказки и подсчитав, какие будут
параметры для вашего варианта.

В случае _функций аннотации_ ситуация похожая, по умолчанию проверяются все решения со страницы заданий, но вы можете
снизить стоимость и увеличить скорость, проверяя только часть решений со страницы (`check_sample`), руководствуясь
интуицией, что, если проверенная часть заданий выполнена качественно, то непроверенная часть тоже будет выполнена
качественно. Заметим, что проверку части решений безопаснее и дешевле применять, если на странице достаточно большое
количество заданий.

### Параметры качества <a name="quality-config"></a>

- `min_confidence` – минимальный уровень уверенности в решении, которого надо достичь.
- `overlap` – перекрытие, бывает двух видов:
    - Статическое перекрытие – число мнений определяется заранее и не меняется (`overlap`).
    - Динамическое перекрытие – число мнений начинается с минимального (`min_overlap`), если после агрегации мнений
      уверенность ниже минимальной (`min_confidence`), то перекрытие увеличивается на единицу и так продолжается вплоть
      до достижения `min_confidence` или максимального перекрытия (`max_overlap`).

<details>

<summary><u>Перекрытие в функциях аннотации</u></summary>

В случае функции аннотации, перекрытие определяется как для аннотаций, так и для их оценок.

Для оценок оно определяется обычным образом, указанным выше.

Для аннотаций перекрытие всегда динамическое, мы начинаем с выдачи задания одному исполнителю, если уверенность в его
решении по оценкам других исполнителей ниже `min_confidence`, мы выдаем задание другому исполнителю, заранее определив
максимальное количество попыток. Минимальное перекрытие фиксируется и равно единице (`min_overlap = 1`), число попыток
соответствует максимальному перекрытию (`max_overlap = attempts_count`).

</details>

- `aggregation_algorithm` – алгоритм агрегации мнений, который по множеству мнений определяет вероятности (`confidence`)
  возможных вариантов. Для функций аннотации этот алгоритм используется при агрегации оценок решений. В данный момент
  поддерживаются следующие алгоритмы:
    - `MAJORITY_VOTE` – выбор решения мнением большинства. Вероятность решения определяется путем деления числа
      проголосовавших на него на общее число голосов.
    - `MAX_LIKELIHOOD` – алгоритм, рассчитывающий веса каждого исполнителя согласно качеству его работы и считающий
      вероятность решений по байесовской формуле полной вероятности.
    - `DAWID_SKENE` – [алгоритм](https://doi.org/10.2307/2346806), рассчитывающий матрицы ошибок исполнителей с помощью
      оценки максимального правдоподобия.
- `correct_control_task_ratio_for_acceptance` – минимальная доля правильно выполненных заданий, необходимая для приема
  решений. В случае функций классификации, это доля среди контрольных заданий, в случае функций аннотации – доля среди
  проверенных решений (`check_sample`).

# Помощь <a name="support"></a>
