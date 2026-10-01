export interface HostelItem {
  id: string;
  name: string;
  code: string;
  type: "BOYS" | "GIRLS" | "CO_ED" | "FACULTY_RESIDENCE";
  wardenName: string;
  wardenPhone: string;
  totalBlocks: number;
  totalRooms: number;
  capacityBeds: number;
  occupiedBeds: number;
  status: "ACTIVE" | "MAINTENANCE";
}

export interface HostelRoomItem {
  id: string;
  hostelName: string;
  block: string;
  floor: number;
  roomNumber: string;
  capacityBeds: number;
  occupiedBeds: number;
  occupants: string[];
  status: "AVAILABLE" | "FULL" | "MAINTENANCE";
}

export interface TransportRouteItem {
  id: string;
  routeCode: string;
  routeName: string;
  vehicleNumber: string;
  driverName: string;
  driverPhone: string;
  capacity: number;
  allocatedStudents: number;
  morningDeparture: string;
  eveningReturn: string;
  stopsCount: number;
  status: "ACTIVE" | "IDLE" | "MAINTENANCE";
}

export interface TransportVehicleItem {
  id: string;
  registrationNumber: string;
  model: string;
  capacitySeats: number;
  fuelType: "DIESEL" | "EV" | "CNG";
  insuranceValidUntil: string;
  status: "IN_SERVICE" | "MAINTENANCE" | "STANDBY";
}

export const MOCK_HOSTELS: HostelItem[] = [
  {
    id: "hst-raman",
    name: "Sir C. V. Raman Hall of Residence",
    code: "HOSTEL-A",
    type: "BOYS",
    wardenName: "Prof. S. K. Patil",
    wardenPhone: "+91 94480 99011",
    totalBlocks: 2,
    totalRooms: 120,
    capacityBeds: 240,
    occupiedBeds: 226,
    status: "ACTIVE",
  },
  {
    id: "hst-kalpana",
    name: "Kalpana Chawla Hall of Residence",
    code: "HOSTEL-B",
    type: "GIRLS",
    wardenName: "Dr. Geeta Pillai",
    wardenPhone: "+91 94480 99012",
    totalBlocks: 2,
    totalRooms: 100,
    capacityBeds: 200,
    occupiedBeds: 188,
    status: "ACTIVE",
  },
  {
    id: "hst-kalam",
    name: "Dr. A. P. J. Abdul Kalam PG Scholars House",
    code: "HOSTEL-C",
    type: "CO_ED",
    wardenName: "Dr. R. Ramanathan",
    wardenPhone: "+91 94480 99013",
    totalBlocks: 1,
    totalRooms: 60,
    capacityBeds: 60,
    occupiedBeds: 54,
    status: "ACTIVE",
  },
];

export const MOCK_HOSTEL_ROOMS: HostelRoomItem[] = [
  {
    id: "rm-304-a",
    hostelName: "Sir C. V. Raman Hall of Residence",
    block: "Block A",
    floor: 3,
    roomNumber: "304",
    capacityBeds: 2,
    occupiedBeds: 2,
    occupants: ["Aarav Patel (24CSE0101)", "Vikramaditya Rao (24AI0301)"],
    status: "FULL",
  },
  {
    id: "rm-214-b",
    hostelName: "Kalpana Chawla Hall of Residence",
    block: "Block B",
    floor: 2,
    roomNumber: "214",
    capacityBeds: 2,
    occupiedBeds: 2,
    occupants: ["Priya Sundaram (24CSE0102)", "Ananya Deshmukh (24ECE0201)"],
    status: "FULL",
  },
  {
    id: "rm-305-a",
    hostelName: "Sir C. V. Raman Hall of Residence",
    block: "Block A",
    floor: 3,
    roomNumber: "305",
    capacityBeds: 2,
    occupiedBeds: 1,
    occupants: ["Rohan Verghese (24CSE0103)"],
    status: "AVAILABLE",
  },
];

export const MOCK_TRANSPORT_ROUTES: TransportRouteItem[] = [
  {
    id: "route-01",
    routeCode: "R-01",
    routeName: "North City Express (Hebbal ↔ Campus)",
    vehicleNumber: "KA-04-E-1892",
    driverName: "D. Gangadhar",
    driverPhone: "+91 98455 12001",
    capacity: 52,
    allocatedStudents: 48,
    morningDeparture: "07:15 AM",
    eveningReturn: "05:15 PM",
    stopsCount: 8,
    status: "ACTIVE",
  },
  {
    id: "route-02",
    routeCode: "R-02",
    routeName: "Metro Corridor (Majestic Station ↔ Campus)",
    vehicleNumber: "KA-01-F-4411",
    driverName: "N. Venkatesh",
    driverPhone: "+91 98455 12002",
    capacity: 52,
    allocatedStudents: 50,
    morningDeparture: "07:00 AM",
    eveningReturn: "05:15 PM",
    stopsCount: 6,
    status: "ACTIVE",
  },
  {
    id: "route-03",
    routeCode: "R-03",
    routeName: "Tech City Feeder (Electronic City ↔ Campus)",
    vehicleNumber: "KA-51-M-8890",
    driverName: "K. Balaraj",
    driverPhone: "+91 98455 12003",
    capacity: 40,
    allocatedStudents: 38,
    morningDeparture: "07:10 AM",
    eveningReturn: "05:15 PM",
    stopsCount: 7,
    status: "ACTIVE",
  },
];

export const MOCK_VEHICLES: TransportVehicleItem[] = [
  {
    id: "veh-01",
    registrationNumber: "KA-04-E-1892",
    model: "Tata Starbus Ultra (52-Seater)",
    capacitySeats: 52,
    fuelType: "DIESEL",
    insuranceValidUntil: "2027-03-31",
    status: "IN_SERVICE",
  },
  {
    id: "veh-02",
    registrationNumber: "KA-01-F-4411",
    model: "Ashok Leyland Sunshine (52-Seater)",
    capacitySeats: 52,
    fuelType: "DIESEL",
    insuranceValidUntil: "2027-05-15",
    status: "IN_SERVICE",
  },
  {
    id: "veh-03",
    registrationNumber: "KA-51-M-8890",
    model: "Eicher Skyline Pro EV (40-Seater Electric)",
    capacitySeats: 40,
    fuelType: "EV",
    insuranceValidUntil: "2027-08-30",
    status: "IN_SERVICE",
  },
];
