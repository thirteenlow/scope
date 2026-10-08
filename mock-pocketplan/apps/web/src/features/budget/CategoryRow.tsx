import type { CategoryAssignment } from "@pocketplan/domain";

export function CategoryRow({ assignment }: { assignment: CategoryAssignment }) {
  const available = assignment.assignedCents - assignment.activityCents;
  return (
    <div className={available < 0 ? "overspent" : "funded"}>
      <strong>{assignment.categoryName}</strong>
      <span>{assignment.assignedCents / 100}</span>
      <span>{assignment.activityCents / 100}</span>
      <span>{available / 100}</span>
    </div>
  );
}

