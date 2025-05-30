from dataclasses import dataclass

from src.models.company import Company
from src.repositories.company_repository import CompanyRepository
from src.repositories.repository import Repository


@dataclass
class UpsertCompany:
    session_id: str
    data: str

    def upsert(self) -> Company:
        instance = Company(session_id=self.session_id, data=self.data)
        try:
            company, _ = Repository(Company).create(instance)
        except Exception:
            company, _ = CompanyRepository(Company).read_by_session_id(
                session_id=self.session_id
            )
            company.data = self.data
            company, _ = Repository(Company).update(company)
        return company
