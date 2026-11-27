/* EXAMPLE — replace with the project's data.
 * The seed of the in-memory store: screens read and change it through ctx.data.
 * Plain JSON-compatible values only (it is cloned and kept in localStorage).
 * Real-looking content in the product's language: names, sums, dates, statuses. */
window.CONCEPT_DATA = {
  user: { name: "Анна Ким" },
  tasks: [
    { id: "t1", title: "Согласовать смету с подрядчиком", due: "2026-12-02", status: "open", owner: "Анна Ким" },
    { id: "t2", title: "Отправить договор на подпись", due: "2026-12-04", status: "open", owner: "Олег Сафин" },
    { id: "t3", title: "Закрыть акт за ноябрь", due: "2026-11-28", status: "done", owner: "Анна Ким" }
  ]
};
