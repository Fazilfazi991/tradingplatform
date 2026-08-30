"use client";

import { Area, AreaChart, CartesianGrid, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const data = [
  ["D-20",1428],["D-18",1441],["D-16",1435],["D-14",1453],["D-12",1459],
  ["D-10",1448],["D-8",1464],["D-6",1472],["D-4",1468],["Now",1482],["D+2",1495],["D+5",1517],
].map(([day,price])=>({day,price}));

export function PriceChart(){return <div className="panel" style={{height:310,padding:"18px 10px 8px"}} aria-label="Synthetic price history and forecast range chart">
  <ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{top:15,right:18,bottom:5,left:0}}>
    <defs><linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#48c78e" stopOpacity={.22}/><stop offset="100%" stopColor="#48c78e" stopOpacity={0}/></linearGradient></defs>
    <CartesianGrid stroke="#20302c" vertical={false}/><XAxis dataKey="day" stroke="#75877e" tickLine={false} axisLine={false} fontSize={10}/><YAxis domain={[1400,1540]} stroke="#75877e" tickLine={false} axisLine={false} fontSize={10} width={42}/>
    <Tooltip contentStyle={{background:"#0d1716",border:"1px solid #33443f",borderRadius:10,fontSize:11}} labelStyle={{color:"#9fb0a6"}}/>
    <ReferenceArea x1="Now" x2="D+5" fill="#e6b35c" fillOpacity={.06} label={{value:"SYNTHETIC FORECAST WINDOW",position:"insideTop",fill:"#e6b35c",fontSize:9}}/>
    <Area type="monotone" dataKey="price" stroke="#48c78e" strokeWidth={2} fill="url(#priceFill)"/>
  </AreaChart></ResponsiveContainer>
</div>}
