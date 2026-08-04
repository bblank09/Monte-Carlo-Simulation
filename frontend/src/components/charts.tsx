// Chart primitives ported from the sibling Backtest Portfolio project's
// RunSummary.tsx (AxisCurve, Histogram, CorrelationMatrix, DataTable, plus
// their helpers). The SVG rendering logic is preserved as-is; only the prop
// interfaces were generalized away from `{ result: BacktestResult }` to
// direct, backtest-agnostic data shapes that map cleanly onto this project's
// SimulateResponse (percentile-keyed series, correlation matrices keyed by
// proj_id, pre-binned histogram rows).

import { useId, useMemo, useRef, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";

const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

export interface ChartPoint {
  x: number;
  y: number;
}

export interface ChartSeries {
  label: string;
  color: string;
  points: ChartPoint[];
  /** Dashed stroke (e.g. for a secondary/benchmark-style series). */
  dashed?: boolean;
  /** Fill the area under the curve down to y=0. */
  area?: boolean;
  /** Formats a single value for the legend/tooltip/axis for this series. */
  valueFormat?: (value: number) => string;
}

export interface TableSection {
  title: string;
  columns: string[];
  rows: (string | number)[][];
}

function slugify(label: string) {
  return label.replace(/[^a-zA-Z0-9]+/g, "-");
}

function lastPoint<T>(items: T[]) {
  return items.length ? items[items.length - 1] : undefined;
}

function humanize(value: string) {
  return value.replace(/_/g, " ");
}

function xForIndex(index: number, length: number) {
  return 70 + (index / Math.max(1, length - 1)) * 780;
}

function prepareSeries(series: ChartSeries[]) {
  const maxLength = Math.max(1, ...series.map((item) => item.points.length));
  const step = Math.max(1, Math.floor(maxLength / 140));
  const sampledSeries = series.map((item) => ({
    ...item,
    points: item.points.filter((_, index) => index % step === 0 || index === item.points.length - 1)
  }));
  const pointCount = Math.max(1, ...sampledSeries.map((item) => item.points.length));
  const allValues = sampledSeries.flatMap((item) => item.points.map((point) => point.y));
  const min = allValues.length ? Math.min(...allValues) : 0;
  const max = allValues.length ? Math.max(...allValues) : 1;
  const range = max - min || 1;
  const yTicks = Array.from({ length: 6 }, (_, index) => {
    const value = min + (range * index) / 5;
    const y = 280 - ((value - min) / range) * 256;
    return { value, y };
  }).reverse();
  const xFor = (index: number, length: number) => 70 + (index / Math.max(1, length - 1)) * 780;
  const yFor = (value: number) => 280 - ((value - min) / range) * 256;
  const paths = sampledSeries.map((item) => {
    const d = item.points.map((point, index) => `${index ? "L" : "M"} ${xFor(index, item.points.length).toFixed(1)} ${yFor(point.y).toFixed(1)}`).join(" ");
    const baselineY = Math.min(280, Math.max(24, yFor(0)));
    const firstX = xFor(0, item.points.length).toFixed(1);
    const lastX = xFor(item.points.length - 1, item.points.length).toFixed(1);
    return {
      label: item.label,
      color: item.color,
      dashed: item.dashed,
      area: item.area,
      d,
      areaD: item.area && item.points.length ? `${d} L ${lastX} ${baselineY.toFixed(1)} L ${firstX} ${baselineY.toFixed(1)} Z` : ""
    };
  });
  const endpoints = sampledSeries.map((item) => {
    const point = lastPoint(item.points) ?? { x: 0, y: 0 };
    return {
      label: item.label,
      color: item.color,
      x: 850,
      y: yFor(point.y)
    };
  });
  const xSource = sampledSeries.reduce((longest, item) => (item.points.length > longest.length ? item.points : longest), [] as ChartPoint[]);
  const xValues = xSource.map((point) => point.x);
  const tickCount = Math.min(6, pointCount);
  const xTicks = Array.from({ length: tickCount }, (_, index) => {
    const pointIndex = tickCount > 1 ? Math.round((index * (pointCount - 1)) / (tickCount - 1)) : 0;
    return { x: xFor(pointIndex, pointCount), value: xValues[pointIndex] ?? 0 };
  });
  const seriesValues = sampledSeries.map((item) => item.points.map((point) => point.y));
  return {
    paths,
    endpoints,
    yTicks,
    xTicks,
    xValues,
    seriesValues,
    pointCount,
    yFor,
    min,
    max,
    latestValue: lastPoint(series[0]?.points ?? [])?.y ?? 0,
    startX: series[0]?.points[0]?.x ?? 0,
    endX: lastPoint(series[0]?.points ?? [])?.x ?? 0
  };
}

export function AxisCurve({
  title,
  series,
  valueFormat,
  xFormat = (value: number) => String(value)
}: {
  title: string;
  series: ChartSeries[];
  valueFormat: (value: number) => string;
  xFormat?: (value: number) => string;
}) {
  const prepared = useMemo(() => prepareSeries(series), [series]);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hover, setHover] = useState<{ index: number; x: number; y: number } | null>(null);
  const gradientId = useId();

  function handleMove(event: ReactMouseEvent<SVGRectElement>) {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const relativeX = ((event.clientX - rect.left) / rect.width) * 880;
    const length = prepared.pointCount;
    const rawIndex = ((relativeX - 70) / 780) * (length - 1);
    const index = Math.min(length - 1, Math.max(0, Math.round(rawIndex)));
    setHover({ index, x: event.clientX - rect.left, y: event.clientY - rect.top });
  }

  const hoverRows = hover
    ? prepared.paths.map((path, seriesIndex) => ({
        label: path.label,
        color: path.color,
        value: (series[seriesIndex]?.valueFormat ?? valueFormat)(prepared.seriesValues[seriesIndex]?.[hover.index] ?? 0)
      }))
    : [];
  const hoverX = hover ? prepared.xValues[hover.index] ?? 0 : 0;
  const hoverPlotX = hover ? xForIndex(hover.index, prepared.pointCount) : 0;

  return (
    <section className="chartPanel">
      <div className="panelHeader compact">
        <div>
          <h3>{title}</h3>
          <p>{xFormat(prepared.startX)} to {xFormat(prepared.endX)}</p>
        </div>
        <span className="badge">{valueFormat(prepared.latestValue)}</span>
      </div>
      <div className="chartLegend">
        {series.map((item) => (
          <span key={item.label}><i style={{ background: item.color }} />{item.label}: {(item.valueFormat ?? valueFormat)(lastPoint(item.points)?.y ?? 0)}</span>
        ))}
      </div>
      <div className="chartCanvas" ref={containerRef}>
        <svg className="axisChart" viewBox="0 0 880 320" role="img" aria-label={title} preserveAspectRatio="none">
          <defs>
            {prepared.paths.filter((path) => path.area).map((path) => (
              <linearGradient id={`${gradientId}-${slugify(path.label)}`} key={path.label} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={path.color} stopOpacity="0.04" />
                <stop offset="100%" stopColor={path.color} stopOpacity="0.4" />
              </linearGradient>
            ))}
          </defs>
          {prepared.yTicks.map((tick) => (
            <g key={tick.value}>
              <line className="gridLine" x1="70" x2="850" y1={tick.y} y2={tick.y} />
              <text className="axisText" x="62" y={tick.y + 4} textAnchor="end">{valueFormat(tick.value)}</text>
            </g>
          ))}
          {prepared.xTicks.map((tick) => (
            <g key={tick.x}>
              <line className="gridLine vertical" x1={tick.x} x2={tick.x} y1="24" y2="280" />
              <text className="axisText" x={tick.x} y="300" textAnchor="middle">{xFormat(tick.value)}</text>
            </g>
          ))}
          <line className="axisLine" x1="70" x2="850" y1="280" y2="280" />
          <line className="axisLine" x1="70" x2="70" y1="24" y2="280" />
          {prepared.paths.filter((path) => path.area).map((path) => (
            <path d={path.areaD} key={`${path.label}-area`} stroke="none" style={{ fill: `url(#${gradientId}-${slugify(path.label)})` }} />
          ))}
          {prepared.paths.map((path) => (
            <path key={path.label} d={path.d} stroke={path.color} strokeDasharray={path.dashed ? "7 7" : undefined} />
          ))}
          {prepared.endpoints.map((point) => (
            <circle key={point.label} cx={point.x} cy={point.y} r="4" fill={point.color} />
          ))}
          {hover ? (
            <g>
              <line className="crosshairLine" x1={hoverPlotX} x2={hoverPlotX} y1="24" y2="280" />
              {prepared.seriesValues.map((values, seriesIndex) => {
                const value = values[hover.index];
                if (value == null) return null;
                return (
                  <circle
                    key={series[seriesIndex]?.label ?? seriesIndex}
                    cx={hoverPlotX}
                    cy={prepared.yFor(value)}
                    r="4.5"
                    fill="#ffffff"
                    stroke={series[seriesIndex]?.color}
                    strokeWidth="2.5"
                  />
                );
              })}
            </g>
          ) : null}
          <rect
            x="70"
            y="24"
            width="780"
            height="256"
            fill="transparent"
            onMouseMove={handleMove}
            onMouseLeave={() => setHover(null)}
          />
        </svg>
        {hover ? (
          <div
            className="chartTooltip"
            style={{ left: Math.min(Math.max(hover.x, 84), (containerRef.current?.clientWidth ?? 880) - 84), top: 8 }}
          >
            <strong>{xFormat(hoverX)}</strong>
            {hoverRows.map((row) => (
              <span key={row.label}><i style={{ background: row.color }} />{row.label}: {row.value}</span>
            ))}
          </div>
        ) : null}
      </div>
      <div className="chartStats">
        <span>Min: {valueFormat(prepared.min)}</span>
        <span>Max: {valueFormat(prepared.max)}</span>
        <span>Latest: {valueFormat(prepared.latestValue)}</span>
      </div>
    </section>
  );
}

function formatCell(value: unknown) {
  if (value == null) return "n/a";
  if (typeof value === "number") {
    if (Math.abs(value) <= 1) return value.toFixed(4);
    if (Number.isInteger(value) && value >= 1000 && value <= 9999) return String(value);
    return number.format(value);
  }
  return String(value);
}

export function DataTable({ section, compact = false, caption }: { section: TableSection; compact?: boolean; caption?: string }) {
  const columns = section.columns;
  const resolvedCaption = section.title || caption;
  return (
    <div className={compact ? "tablePanel compactTable" : "tablePanel"}>
      {section.title ? <h3>{section.title}</h3> : null}
      <div className="tableScroller">
        <table>
          {resolvedCaption ? <caption className="srOnly">{resolvedCaption}</caption> : null}
          <thead>
            <tr>{columns.map((column) => <th key={column}>{humanize(column)}</th>)}</tr>
          </thead>
          <tbody>
            {section.rows.map((row, index) => (
              <tr key={index}>
                {columns.map((column, columnIndex) => <td key={column}>{formatCell(row[columnIndex])}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <small>{section.rows.length} row{section.rows.length === 1 ? "" : "s"}</small>
    </div>
  );
}

export interface HistogramBin {
  bin: string;
  count: number;
  from: number;
  to: number;
}

const pct = new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 2 });

export function Histogram({ rows }: { rows: HistogramBin[] }) {
  const maxCount = Math.max(...rows.map((row) => row.count), 1);
  return (
    <div className="histWrap">
      <div className="histLegend">
        <span><i className="histSwatch histSwatch-loss" /> Loss</span>
        <span><i className="histSwatch histSwatch-gain" /> Gain</span>
      </div>
      <div className="hist" role="img" aria-label={`Distribution histogram: ${rows.map((row) => `${row.bin}, ${row.count}`).join("; ")}`}>
        {rows.map((row) => (
          <div className="histCol" key={row.bin}>
            <span aria-hidden="true" className="histCount">{row.count || ""}</span>
            <div
              aria-hidden="true"
              className={row.from >= 0 ? "histBar histBar-gain" : "histBar histBar-loss"}
              style={{ height: `${Math.max(5, (row.count / maxCount) * 92)}px` }}
              title={`${row.bin}: ${row.count}`}
            />
            <span aria-hidden="true" className="histAxisLabel">{pct.format(row.from)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function correlationColor(value: number) {
  const opacity = Math.max(0.14, Math.min(0.85, Math.abs(value)));
  return value >= 0 ? `rgb(19 122 79 / ${opacity})` : `rgb(180 35 24 / ${opacity})`;
}

export interface CorrelationData {
  /** Ordered list of asset ids that make up the matrix's rows/columns. */
  ids: string[];
  /** Optional display name lookup; falls back to the raw id when absent. */
  displayNameById?: Record<string, string>;
  /** Correlation lookup keyed [rowId][colId] -> value (null when unavailable). */
  correlation: Record<string, Record<string, number | null>>;
}

export function CorrelationMatrix({ ids, displayNameById = {}, correlation }: CorrelationData) {
  return (
    <div className="tableScroller">
      <table className="correlationMatrix">
        <caption className="srOnly">Correlation matrix between every pair of holdings</caption>
        <thead>
          <tr>
            <th scope="col" />
            {ids.map((id) => <th key={id} scope="col">{displayNameById[id] ?? id}</th>)}
          </tr>
        </thead>
        <tbody>
          {ids.map((rowId) => (
            <tr key={rowId}>
              <th scope="row">{displayNameById[rowId] ?? rowId}</th>
              {ids.map((colId) => {
                const value = rowId === colId ? 1 : correlation[rowId]?.[colId] ?? null;
                return (
                  <td key={colId} style={{ background: value == null ? undefined : correlationColor(value) }}>
                    {value == null ? "n/a" : number.format(value)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
