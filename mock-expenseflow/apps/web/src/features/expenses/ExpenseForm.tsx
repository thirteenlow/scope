import { useState } from "react";
import type { Expense, ExpenseInput } from "@expenseflow/shared-types";

type Props = {
  expense: Expense;
  onSave(input: ExpenseInput): Promise<void>;
};

export function ExpenseForm({ expense, onSave }: Props) {
  const [description, setDescription] = useState(expense.description);
  const [amount, setAmount] = useState(expense.amount);
  const editable = expense.status === "DRAFT";

  return (
    <form onSubmit={(event) => {
      event.preventDefault();
      void onSave({ ...expense, description, amount });
    }}>
      <input value={description} disabled={!editable} onChange={(event) => setDescription(event.target.value)} />
      <input value={amount} disabled={!editable} type="number" onChange={(event) => setAmount(Number(event.target.value))} />
      {editable ? <button type="submit">Save draft</button> : <p>This expense can no longer be edited.</p>}
    </form>
  );
}

