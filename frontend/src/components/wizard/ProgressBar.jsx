// src/components/wizard/ProgressBar.jsx
import React from "react";

const steps = [
  { id: 1, name: "ภาษี/การจัดส่ง" },
  { id: 3, name: "ข้อมูลลูกค้า" },
  { id: 4, name: "สรุปรายการ" }, // Step 4, 5, 6 รวมกัน
];

const ProgressBar = ({ currentStepId = 1 }) => {
  let activeStep = steps.find((s) => s.id === currentStepId);
  // ถ้ารายการปัจจุบันคือ 4, 5, หรือ 6 ให้ Active ที่ "สรุปรายการ"
  if (currentStepId >= 4) {
    activeStep = steps.find((s) => s.id === 4);
  }

  return (
    <nav className="mb-6">
      <ol className="flex items-center space-x-2 rounded-lg border border-gray-200 bg-gray-50 p-3 shadow-sm">
        {steps.map((step, index) => {
          const isCompleted = activeStep ? step.id < activeStep.id : false;
          const isCurrent = activeStep ? step.id === activeStep.id : false;

          return (
            <li key={step.id} className="flex-1">
              <div
                className={`flex w-full flex-col items-center justify-center rounded-md p-3 ${
                  isCurrent
                    ? "border-2 border-blue-600 bg-blue-100"
                    : isCompleted
                      ? "bg-green-100"
                      : "bg-gray-100"
                }`}
              >
                {isCompleted ? (
                  <span className="text-sm font-bold text-green-700">{step.name}</span>
                ) : isCurrent ? (
                  <span className="text-sm font-bold text-blue-700">{step.name}</span>
                ) : (
                  <span className="text-sm font-bold text-gray-500">{step.name}</span>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default ProgressBar;
