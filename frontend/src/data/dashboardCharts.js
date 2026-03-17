export const dashboardCharts = [
  {
    title: "Production mensuelle",
    type: "line",
    data: {
      labels: ["Jan", "Fev", "Mar", "Avr", "Mai", "Juin"],
      datasets: [
        {
          label: "Production (t)",
          data: [120, 140, 130, 160, 180, 210],
          borderColor: "#2E7D32",
          backgroundColor: "rgba(46, 125, 50, 0.2)",
        },
      ],
    },
  },
  {
    title: "Performance recolteurs",
    type: "bar",
    data: {
      labels: ["Kouassi", "Yao", "Traore", "Konan"],
      datasets: [
        {
          label: "Tonnage (t)",
          data: [42, 37, 50, 48],
          backgroundColor: "#66BB6A",
        },
      ],
    },
  },
  {
    title: "Prediction IA",
    type: "line",
    data: {
      labels: ["J1", "J2", "J3", "J4", "J5"],
      datasets: [
        {
          label: "Reel",
          data: [40, 45, 42, 50, 55],
          borderColor: "#2E7D32",
        },
        {
          label: "Prevu",
          data: [38, 43, 44, 48, 53],
          borderColor: "#FBC02D",
        },
      ],
    },
  },
];
