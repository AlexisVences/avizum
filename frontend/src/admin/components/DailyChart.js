import React from 'react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const dayLabel = (iso, options) => {
    const [y, m, d] = iso.split('-').map(Number);
    return new Intl.DateTimeFormat('es-MX', { timeZone: 'UTC', ...options }).format(new Date(Date.UTC(y, m - 1, d)));
};

const short = (iso) => dayLabel(iso, { day: 'numeric', month: 'short' });
const long = (iso) => dayLabel(iso, { day: 'numeric', month: 'long', year: 'numeric' });

const DailyChart = ({ points }) => (
    <figure className="tw-m-0">
        <div className="tw-h-64 tw-w-full" aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={points} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
                    <CartesianGrid stroke="#DDD8CC" vertical={false} />
                    <XAxis
                        dataKey="date"
                        tickFormatter={short}
                        stroke="#52544D"
                        tick={{ fontSize: 12, fill: '#52544D' }}
                        minTickGap={24}
                    />
                    <YAxis allowDecimals={false} stroke="#52544D" tick={{ fontSize: 12, fill: '#52544D' }} />
                    <Tooltip
                        labelFormatter={long}
                        formatter={(value) => [value, 'Preguntas']}
                        contentStyle={{ borderRadius: 6, borderColor: '#DDD8CC', fontSize: 13 }}
                    />
                    <Line
                        type="linear"
                        dataKey="questions"
                        stroke="#1C3F94"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4 }}
                        isAnimationActive={false}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
        <table className="tw-sr-only">
            <caption>Preguntas por día</caption>
            <thead>
                <tr>
                    <th scope="col">Día</th>
                    <th scope="col">Preguntas</th>
                </tr>
            </thead>
            <tbody>
                {points.map((point) => (
                    <tr key={point.date}>
                        <th scope="row">{long(point.date)}</th>
                        <td>{point.questions}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    </figure>
);

export default DailyChart;
