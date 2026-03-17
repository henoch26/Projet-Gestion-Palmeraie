import { useEffect,useRef } from "react";
import { Chart } from "chart.js/auto";

export default function ChartCard({title,type,data,options}){

    // creation des references persistantes
    const canvasRef = useRef(null);         //Permet d'acceder a l'element canvas dans le DOM
    const chartRef = useRef(null);           //Sert a stocker le graphique

    useEffect(()=>{
        if (!canvasRef.current) return;     //On arrete tout si canvasRef n'existe pas

        if (chartRef.current){                  //On detruit le graphique existant
            chartRef.current.destroy();          //pour ne pas avoir de superposition de graphique
        }

        // creation d'un nouveau graphique

        chartRef.current = new Chart(canvasRef.current,{
            type,data,options,
        });

        return () => chartRef.current?.destroy();
    },[type,data,options]);

    return (
            <div className="chart-card">
                <h3>{title}</h3>
                <canvas ref={canvasRef} />
            </div>
        );



}