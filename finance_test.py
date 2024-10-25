import sys

import matplotlib.pyplot as plt
import numpy_financial as npf

from functools import reduce
from collections.abc import Iterable

"""
Module for simulating the Dutch tax-deducible retirement savings and returns

Disclaimer: Do not use for any form of financial advise!

This script aims to provide personal insight in government tax rules described here:
https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/prive/werk_en_inkomen/lijfrente/
"""

class SavingContract:
  """Class representing tax-deducible, fixed-interest savings over a fixed period of time"""

  def __init__(self, savings, contribution, interestRate, duration, taxRate):
    self._savings = savings
    self._contributions = contribution
    self._interestRate = interestRate
    self._duration = duration
    self._taxRate = taxRate

  def print(self):
    """Print details of the savings contract"""
    profit = self._savings - self._contributions
    profit_percentage = profit * 100 / self._savings

    print(f"Total savings: {self._savings:.0f} euro;\n",
      f"Total contribution: {self._contributions:.0f} euro ({self._taxRate * 100:.1f}% tax deducted);\n",
      f"Gross profit: {profit:.0f} euro",
      f"\n\t\t{profit_percentage:.1f}% over {self._duration} years;",
      f"\n\t\t{self._interestRate * 100:.1f}% per year")

  def plot(self):
    """Plot the savings progress per time unit using Matplotlib"""
    t_saving = range(1, self._duration + 1)
    fv_saving_sequence = [
      npf.fv(self._interestRate, i, -1 * self._contributions / self._duration, 0)
      for i in t_saving ]

    plt.scatter(t_saving, fv_saving_sequence)

def accumulateSavingsContracts(savingContracts: Iterable[SavingContract]) -> SavingContract:
  """ Returns an aggregated SavingsContract instance from a sequence of contracts"""

  def getTotalSavings(savingContracts: Iterable[SavingContract]) -> float:
    """Returns accumulated savings from a sequence of contracts"""
    def accumulate_contracts(acc: float, x: SavingContract) -> float:
      """Adds the gross contract contributions of instance x to the total accumulated contributions"""
      return npf.fv(x._interestRate, x._duration, -1 * x._contributions, -1 * acc - x._savings)
    return reduce(accumulate_contracts, savingContracts, 0)

  def getTotalOwnContributions(savingsContracts: Iterable[SavingContract]) -> float:
    """Returns accumulated tax-deducted (net) contributed deposits from a sequence of contracts"""
    def accumulate_contracts(acc: float, x: SavingContract) -> float:
      """Adds the net contract contributions of instance x to the total accumulated contributions"""
      return acc + (x._contributions * x._duration * (1 - x._taxRate))
    return reduce(accumulate_contracts, savingsContracts, 0)

  def getTotalContributions(savingsContracts: Iterable[SavingContract]) -> float:
    """Returns accumulated gross contributed deposits of a sequence of contracts"""
    return reduce(lambda acc, x : acc + (x._contributions * x._duration), savingsContracts, 0)

  total_savings = getTotalSavings(savingContracts)
  total_contributions = getTotalContributions(savingContracts)
  total_own_contributions = getTotalOwnContributions(savingContracts)
  duration = reduce(lambda acc, x : acc + x._duration, savingContracts, 0)
  rate = npf.rate(duration, -1 * total_own_contributions / duration, 0, total_savings, tol=1e-3)
  tax_rate = 1 - total_own_contributions / total_contributions
  return SavingContract(total_savings, total_own_contributions, rate, duration, tax_rate)

class RetirementContract:
  """Class representing retirement incomes from a gross fixed-interest deposit"""
  def __init__(self, interestRate, deposit, duration, taxRate):
    self._interestRate = interestRate
    self._savings = deposit
    self._duration = duration
    self._taxRate = taxRate

  def grossYearlyIncome(self) -> float:
    """Returns the gross yearly return, so that savings are depleted after the contract years"""
    return npf.pmt(self._interestRate, self._duration, -1 * self._savings)

  def print(self):
    """Print details of the retirements contract"""
    gross_yearly_income = self.grossYearlyIncome()
    gross_monthly_income = gross_yearly_income / 12
    net_monthly_income = (1 - self._taxRate) * gross_monthly_income

    print(f"Yearly gross income: {gross_yearly_income:.0f} euro")
    print(f"Monthly gross income: {gross_monthly_income:.0f} euro")
    print(f"Monthly net income: {net_monthly_income:.0f} euro")

    # Totals:
    total_net_payout = net_monthly_income * 12 * self._duration
    overall_tax_rate = (self._savings - total_net_payout) / self._savings
    print(f"Net profit: {total_net_payout:.0f} euro of {self._savings:.0f} euro gross")
    print(f"\t\tTax rate: {overall_tax_rate * 100:.1f}%")

  def plot(self, time_offset = 0):
    """Plot the remaining fund per time unit during retirement using Matplotlib"""
    t_income = range(1, self._duration + 1)
    fv_income_sequence = [
      npf.fv(self._interestRate, i, self.grossYearlyIncome(), -1 * self._savings)
      for i in t_income ]

    # Apply time-offset for plotting
    t = list(map(lambda x : x + time_offset, t_income))
    plt.scatter(t, fv_income_sequence)

def main() -> int:
  """Main program for simulating a retirement plan"""
  # fill the savings contracts
  saving_contracts = []

  # Example - Lijfrente calculation
  # 
  # 40-year old person retiring at age 69:
  # - Current savings are 1000 euros;
  # - Save 100 euros per month -> 1200 euros per year (20 years long)
  # - Wait for 9 years before retirement.
  # - Consume retirement savings over a period of 20 years

  # Initial deposit
  interest_rate = 0.02
  income_tax_rate = 0.37
  initial_contributions = 1000
  saving_contracts.append( SavingContract(0, initial_contributions, interest_rate, 1, income_tax_rate) )

  # Yearly contributions:
  yearly_contribution = 1200
  contribution_duration = 20
  saving_contracts.append( SavingContract(0, yearly_contribution, interest_rate, contribution_duration, income_tax_rate) )

  # Interest only; Period without contributions:
  idle_duration = 9
  saving_contracts.append( SavingContract(0, 0, interest_rate, idle_duration, income_tax_rate) )

  # Execute all savings:
  total_savings = accumulateSavingsContracts(saving_contracts)
  total_savings.print()

  # Pension time... payout:
  savings_rate = 0.03
  pay_duration = 20
  pay_tax_rate = 0.19

  retirement_contract = RetirementContract(savings_rate, total_savings._savings, pay_duration, pay_tax_rate)
  retirement_contract.print()

  # Plot both schemes after each other
  plt.xlabel("time (years)")
  plt.ylabel("Gross savings (euro)")
  total_savings.plot()
  retirement_contract.plot(total_savings._duration)
  plt.show()

  return 0

if __name__ == '__main__':
  sys.exit(main())
