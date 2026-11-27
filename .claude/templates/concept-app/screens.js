/* EXAMPLE — replace with the project's screens (split into screens-<area>.js when it grows;
 * add each file to index.html after data.js).
 *
 * One Concept.screen() per screen. render(ctx) returns an HTML string built from ctx.data;
 * actions change ctx.data — the runtime saves and re-renders. Escape every data value with ctx.esc(). */

Concept.setup({ project: "Пример: задачи команды", version: "v1", start: "tasks", nav: "top" });

Concept.screen({
  id: "S1",
  name: "tasks",
  title: "Задачи",
  note: "Список задач команды, отметка «сделано», переход в задачу",
  nav: true,
  render: function (ctx) {
    var e = ctx.esc;
    var rows = ctx.data.tasks.map(function (t) {
      return '<div>' +
        '<input type="checkbox" data-action="toggle" data-id="' + e(t.id) + '"' + (t.status === "done" ? " checked" : "") + ">" +
        '<a class="c-grow" href="' + e(ctx.href("task", { id: t.id })) + '">' + e(t.title) + "</a>" +
        '<span class="c-muted">' + e(t.due) + "</span>" +
        '<span class="c-tag">' + (t.status === "done" ? "сделано" : "в работе") + "</span>" +
        "</div>";
    }).join("");
    return '<div class="c-toolbar"><h1 class="c-grow">Задачи</h1>' +
      '<button class="c-btn" data-stub="Фильтр по исполнителю и сроку">Фильтр</button>' +
      '<a class="c-btn-primary" href="#/task-new">Новая задача</a></div>' +
      '<div class="c-list">' + (rows || '<div class="c-muted">Задач нет</div>') + "</div>";
  },
  actions: {
    toggle: function (ctx, arg) {
      var t = ctx.data.tasks.filter(function (x) { return x.id === arg.id; })[0];
      if (t) t.status = t.status === "done" ? "open" : "done";
    }
  }
});

Concept.screen({
  id: "S2",
  name: "task",
  title: "Задача",
  note: "Карточка задачи: срок, исполнитель, удаление",
  parent: "tasks",
  sample: { id: "t1" },
  render: function (ctx) {
    var e = ctx.esc;
    var t = ctx.data.tasks.filter(function (x) { return x.id === ctx.params.id; })[0];
    if (!t) return '<div class="c-empty">Задача не найдена. <a href="#/tasks">К списку</a></div>';
    return '<p><a href="#/tasks">← Задачи</a></p><h1>' + e(t.title) + "</h1>" +
      '<div class="c-split"><div class="c-card">' +
      "<p><span class=\"c-muted\">Срок:</span> " + e(t.due) + "</p>" +
      "<p><span class=\"c-muted\">Исполнитель:</span> " + e(t.owner) + "</p>" +
      '<div class="c-box">Комментарии и вложения</div></div>' +
      '<div class="c-col">' +
      '<button class="c-btn" data-stub="Передать задачу другому исполнителю">Передать</button>' +
      '<button class="c-btn" data-action="remove">Удалить</button></div></div>';
  },
  actions: {
    remove: function (ctx) {
      ctx.data.tasks = ctx.data.tasks.filter(function (x) { return x.id !== ctx.params.id; });
      ctx.toast("Задача удалена");
      ctx.go("tasks");
    }
  }
});

Concept.screen({
  id: "S3",
  name: "task-new",
  title: "Новая задача",
  note: "Форма создания задачи",
  parent: "tasks",
  render: function (ctx) {
    return '<p><a href="#/tasks">← Задачи</a></p><h1>Новая задача</h1>' +
      '<form class="c-card" data-submit="create" style="max-width:520px">' +
      '<label class="c-field"><span>Что сделать</span><input name="title" required></label>' +
      '<label class="c-field"><span>Срок</span><input name="due" type="date"></label>' +
      '<button class="c-btn-primary">Создать</button></form>';
  },
  actions: {
    create: function (ctx, values) {
      ctx.data.tasks.unshift({
        id: ctx.uid(), title: values.title, due: values.due || "без срока", status: "open", owner: ctx.data.user.name
      });
      ctx.go("tasks");
    }
  }
});

Concept.scenario({
  title: "Завести задачу и закрыть её",
  steps: [
    { text: "Открыть список задач", go: "tasks" },
    "Нажать «Новая задача», заполнить, создать",
    "Отметить новую задачу галочкой — статус меняется на «сделано»"
  ]
});
