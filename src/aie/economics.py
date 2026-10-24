from decimal import Decimal
def required_calls(target_daily_net,price,facilitator_rate='0',facilitator_fixed='0',marginal_cost='0',daily_fixed_cost='0'):
 margin=Decimal(price)*(1-Decimal(facilitator_rate))-Decimal(facilitator_fixed)-Decimal(marginal_cost)
 if margin<=0:return None
 return int(((Decimal(target_daily_net)+Decimal(daily_fixed_cost))/margin).to_integral_value(rounding='ROUND_CEILING'))
def scenario(price,calls,facilitator_rate='0',facilitator_fixed='0',marginal_cost='0',fixed_cost='0'):
 p=Decimal(price);n=Decimal(calls);fees=(Decimal(facilitator_rate)*p+Decimal(facilitator_fixed))*n;cost=Decimal(marginal_cost)*n+Decimal(fixed_cost);net=p*n-fees-cost;margin=p*(1-Decimal(facilitator_rate))-Decimal(facilitator_fixed)-Decimal(marginal_cost)
 return {'gross':p*n,'fees':fees,'costs':cost,'net':net,'per_call_margin':margin,'break_even_calls':None if margin<=0 else (Decimal(fixed_cost)/margin).to_integral_value(rounding='ROUND_CEILING')}
