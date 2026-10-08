import type { BudgetMonth as Month } from "@pocketplan/domain";
import { CategoryRow } from "./CategoryRow";

export function BudgetMonth({ month }: { month: Month }) {
  return (
    <main>
      <header>
        <h1>{month.label}</h1>
        <p>{month.availableToAssignCents / 100} available to assign</p>
      </header>
      {month.categories.map((category) => (
        <CategoryRow key={category.categoryId} assignment={category} />
      ))}
    </main>
  );
}

