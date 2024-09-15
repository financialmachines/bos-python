# BatteryOS API Wrapper

## Calc

– slug<br>
– iso<br>
– name<br>
– user<br>
– category<br>
– status<br>
– refdate: datetime<br>
– startdate: datetime<br>
– enddate: datetime<br>
– data: {data_slug: [Data](#data), ...}<br>
– nodes: {node_slug: [Node](#node), ...}<br>
– scenarios: {scenario_slug: [Scenario](#scenario), ...}<br>
– node_scenarios: {node_scenario_slug: [NodeScenario](#nodescenario), ...}

– `set_user(email)`

## Node

– calc: [Calc](#calc)<br>
– slug<br>
– iso<br>
– name<br>
– category

## Scenario

– calc: [Calc](#calc)<br>
– slug<br>
– name<br>
– params: [ScenarioParams](#scenarioparams)

## NodeScenario

– calc: [Calc](#calc)<br>
– slug<br>
– node: [Node](#node)<br>
– scenario: [Scenario](#scenario)<br>
– params: [ScenarioParams](#scenarioparams)<br>
– status<br>
– results (TBD)

## ScenarioParams

## Data

– slug<br>
– iso<br>
– node: [Node](#node)<br>
– datatype<br>
– fromdate<br>
– todate
