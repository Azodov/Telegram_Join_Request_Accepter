from loader import dp
from .admins import IsSuperAdmin, IsChannelExist

if __name__ == "filters":
    dp.filters_factory.bind(IsSuperAdmin)
    dp.filters_factory.bind(IsChannelExist)
